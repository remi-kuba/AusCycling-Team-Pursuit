# TODO: determine how data will be imported and used
import matplotlib.pyplot as plt
import csv
import itertools
from enum import Enum
import pandas as pd
from scipy import interpolate
import math
import numpy


class Position(Enum):
    First: 1
    Second: 2
    Third: 3
    Fourth: 4


class RiderData:
    def __init__(self, drags, areas, curves, ):
        self.power_percent = {0: 0.95,
                              1: 0.7,
                              2: 0.65,
                              3: 0.6}
        self.air_density = 1.225

        # TODO: fix the velocity and time_125 setting
        self.velocity = 1
        self.time_125 = 12.5

        self.drags = drags
        self.areas = areas
        self.curves = curves
        self.leader = 0
        self.time = 0
        self.distance = 4000

    def get_drag(self, rider):
        return self.drags[rider]

    def get_area(self, rider):
        return self.areas[rider]

    def set_velocity_time(self, velocity):
        self.velocity = velocity
        self.time_125 = 125 / velocity

    def get_curve(self, rider):
        return self.curves[rider]

    def get_curve_point(self, rider, time):
        curve = self.get_curve(rider)
        return curve(time)

    def calculate_power(self, rider, position):
        return (0.5 * self.air_density * (self.velocity ** 3) * self.get_area(rider)
                * self.get_drag(rider) * self.power_percent[position])

    def new_leader(self):
        self.leader = (self.leader + 1) % 4

    def old_leader(self):
        self.leader = (self.leader - 1) % 4

    def get_switch_number(self):
        distance_travelled = 4000 - self.distance
        switch_number = distance_travelled / 125
        return int(switch_number)

    def update_w_primes(self, w_primes):
        leader = self.leader
        new_w_primes = [0] * 4
        for position in range(4):
            rider = (leader + position) % 4
            power = self.calculate_power(rider, position)
            # the rectangle part of the power curve
            work_depleted = self.get_curve_point(rider, power) * self.time_125
            new_w_primes[rider] = w_primes[rider] - work_depleted
        return new_w_primes

    def make_copy(self):
        new_drags = [i for i in self.drags]
        new_areas = [i for i in self.areas]
        new_curves = [i for i in self.curves]
        return RiderData(new_drags, new_areas, new_curves)


def all_orderings(num_riders):
    """
    riders are labeled based off of the data arrays (rider0, rider1, ...)
    :param num_riders: number of riders that could possibly participate in team pursuit
    :return: all permutations of a 4-rider team pursuit starting order
    """
    first_order = [i for i in range(num_riders)]
    orderings = itertools.combinations(first_order, 4)
    return [p for p in orderings]


def find_optimal_ordering(num_riders, drags, areas, w_primes, power_curves):
    orders = all_orderings(num_riders)
    times = {}
    # try out each order
    for order in orders:
        # get the drag, area, and W' of the four riders
        drag = [drags[i] for i in order]
        area = [areas[i] for i in order]
        w_prime = [w_primes[i] for i in order]
        curves = [power_curves[i] for i in order]
        riders = RiderData(drag, area, curves)
        times[order] = minimize_time(riders, w_prime)
    # return the order:(time, switches) key-value pair with the fastest time
    # return min(times.items(), key= lambda t: t[1][0])
    return times


def next_leader(leader):
    return (leader + 1) % 4


def invalid_w_prime(w_primes):
    for w in w_primes:
        if w < 0:
            return True
    return False


def minimize_time(riders, w_primes, switches=None):
    """
    :return: minimized time and the array of switching places that minimizes the time over the 4km
    """
    if not switches:
        switches = []
    if invalid_w_prime(w_primes):
        return float('inf'), []
    if not riders.distance:
        return riders.time, switches

    riders.distance -= 125
    riders.time += riders.time_125
    new_w_primes = riders.update_w_primes(w_primes)

    riders.new_leader()
    switch_now = minimize_time(riders, new_w_primes, switches)
    riders.old_leader()
    no_switch = minimize_time(riders, new_w_primes, switches)

    time = no_switch[0]
    rest_of_switches = no_switch[1]
    if switch_now[0] < no_switch[0]:
        switches.append(riders.get_switch_number())
        rest_of_switches = switch_now[1]
        time = switch_now[0]

    switches.extend(rest_of_switches)
    #
    # riders.distance += 125
    # riders.time -= riders.time_125

    return time + riders.time, switches


def main():
    drags = [0.6, 0.61, 0.62, 0.58, 0.6, 0.6]
    # in m^2
    areas = [0.36, 0.35, 0.355, 0.372, 0.355, 0.352]
    # in Joules
    ws = [50000, 52000, 50000, 51000, 50080, 50100]

    df = pd.read_csv('../power_curves.csv')
    print(df.keys())
    x = df['Time (s)'].to_numpy()
    y = df['W4'].to_numpy()
    # y = numpy.array([math.log(a) for a in y])
    # y = pd.DataFrame.apply(y, lambda a: math.log(a))

    i = interpolate.InterpolatedUnivariateSpline(x, y)

    time, power = [], []

    # print(find_optimal_ordering(6, drags, areas, ws, [i]*6))

    with open('../power_curves.csv', 'r') as File:
        plots = csv.reader(File, delimiter=',')
        next(plots)
        for row in plots:
            time.append(float(row[0]))
            power.append(float(row[8]))
    for j in range(0, 3500, 1):
        time.append(j)
        power.append(i(j))
    plt.scatter(time, power, color='g', s=20)
    plt.xlabel('Time')
    plt.ylabel('Power')
    plt.title('Power Curve')
    plt.show()
    # print(i(3500))


if __name__ == "__main__":
    main()

