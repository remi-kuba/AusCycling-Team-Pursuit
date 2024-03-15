import pandas as pd
from scipy import interpolate
import csv


TEAM_PURSUIT_DISTANCE = 4000
POWER_CURVE = "../power_curves.csv"


def minimize_time(riders, order, works, velocity, curves, drag_areas, time, distance, switches = None):
    """
    :param riders: list of the 4 riders in the team
    :param order: dict with key = rider number, val = order number
    :param works: dict with key = rider number, val = work
    :param velocity: constant velocity throughout calculation
    :param curves: dict with key = rider number, val = power curve file name
    :param areas: dict with key = rider number, val = rider area
    :param drags: dict with key = rider number, val = drag amount
    :param time: current time spent on team pursuit
    :return: {'time': minimized time, 'switches': [area1, area2, ...]}
    """
    if not switches:
        switches = []
    if not distance:
        return {'time': time, 'switches': switches}

    time_over_125 = 125 / velocity
    powers = {rider: calculate_power(order[rider], velocity, drag_areas[rider]) for rider in riders}
    new_works = {}
    for rider in riders:
        good_power = check_power(curves[rider], time_over_125, powers[rider])
        new_work = works[rider] - powers[rider] * time_over_125
        good_work = check_work(new_work)
        if not good_work or not good_power:
            return {'time': float('inf'), 'switches': []}
        new_works[rider] = new_work

    new_time = time + time_over_125
    new_distance = distance - 125
    current_switch_area = int((TEAM_PURSUIT_DISTANCE - new_distance) / 125)
    switched_order = {r: (position - 1) % 4 for r, position in order.items()}
    with_switch = [i for i in switches] + [current_switch_area]
    switches.append(current_switch_area)
    # TODO: Actually calculate the switch_time variable
    switch_time = 0.1
    switch = minimize_time(riders, switched_order, new_works, velocity, curves, drag_areas,
                           new_time + switch_time, new_distance, with_switch)
    without_switch = [i for i in switches]
    no_switch = minimize_time(riders, order, new_works, velocity, curves, drag_areas,
                           new_time, new_distance, without_switch)

    # print(switch, no_switch)
    print(switches)
    print(f"""Switch {distance}: {switch}\nNo Switch: {distance}: {no_switch}\n""")
    # TODO: turn this into a maximize power spent
    return min([switch, no_switch], key=lambda x: x['time'])


def check_power(curve, time, power):
    return get_power(curve, time) >= power


def check_work(work):
    return work > 0


def get_power(curve, time):
    # TODO: read curve and return power
    df = pd.read_csv(POWER_CURVE)
    x = df["Time (s)"].to_numpy()
    y = df[curve].to_numpy()
    interpolated = interpolate.InterpolatedUnivariateSpline(x,y)
    return interpolated(time)
    # return 10000


def calculate_power(position, velocity, area_drag):
    power_percent = {0: 0.95,
                     1: 0.7,
                     2: 0.65,
                     3: 0.6}
    air_density = 1.225
    return (0.5 * air_density * (velocity ** 3) * area_drag
            * power_percent[position])


def main():
    riders = [0, 1, 2, 3]
    order = {i: i for i in riders}
    work_list = [360000, 5000000, 5000000, 5200000]
    works = {i: work_list[i] for i in riders}
    velocity = 10
    curves = {i: "W" + str(i + 1) for i in riders}
    drag_area_list = [0.36, 0.35, 0.355, 0.372, 0.355, 0.352]
    drag_areas = {i: drag_area_list[i] for i in riders}
    # drag_list = [0.6, 0.61, 0.62, 0.58, 0.6, 0.6]
    # drags = {i: drag_list[i] for i in riders}
    start_time = 0
    start_distance = TEAM_PURSUIT_DISTANCE
    # start_distance =
    # print('\n\n\n\n')
    print(minimize_time(riders, order, works, velocity, curves, drag_areas, start_time, start_distance))
    # print(calculate_power(3, 10, 0.36, 0.6) * 12.5)


if __name__ == "__main__":
    main()
