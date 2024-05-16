import gurobipy as gp
from gurobipy import GRB
import numpy as np
from scipy.interpolate import interp1d
from itertools import permutations
import csv
import os


# Unchanging variables
def run():
    num_cyclists = 4
    num_bends = 32
    drags = [.96, .58, .52, .53]

    # time = [1,5,10,20,30,45,60,120,150,180,240,300,360,480,600,720,900,1200,2400,3600]

    half_lap_distance = 125
    penalty_distance = 2.1
    rho = 1.225
    cyclists_init_order = [0,1,2,3]

    critical_power_from_csv = []
    w_prime_from_csv = []
    CdA_from_csv = []
    m_from_csv = []
    time = []
    rider_names = []
    absolute_path = os.path.dirname(os.path.abspath(__file__))
    phys_file_path = os.path.join(absolute_path, "physiology.csv")
    with open(phys_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row_number, row in enumerate(reader):
            if row_number >= 4:
                break
            rider_names.append(row['Name'])
            critical_power_from_csv.append(float(row['CP']))
            w_prime_from_csv.append(float(row["W'"])*1000)
            CdA_from_csv.append(float(row['CdA']))
            m_from_csv.append(float(row['m']))
    team_w_prime = sum(w_prime_from_csv)
    raw_power_curves_from_csv = []
    pc_file_path = os.path.join(absolute_path, "power_curve.csv")
    with open(pc_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        m1 = []
        m2 = []
        m3 = []
        m4 = []
        for row in reader:
            time.append(float(row['Time (s)']))
            m1.append(float(row[rider_names[0]]))
            m2.append(float(row[rider_names[1]]))
            m3.append(float(row[rider_names[2]]))
            m4.append(float(row[rider_names[3]]))

    raw_power_curves_from_csv.append(m1)
    raw_power_curves_from_csv.append(m2)
    raw_power_curves_from_csv.append(m3)
    raw_power_curves_from_csv.append(m4)


    def initialize_W_depleted_matrix(half_lap_time, velocity_m_per_sec, critical_power, w_prime, CdA, raw_power_curves, num_half_laps_to_accel):
        num_bends_steady_state = num_bends - num_half_laps_to_accel
        max_power = np.zeros((num_cyclists, num_bends_steady_state, num_bends_steady_state))
        W_depleted = np.zeros((num_cyclists, len(drags), num_bends_steady_state, num_bends_steady_state))
        penalty_time = (penalty_distance * half_lap_time) / half_lap_distance

        for cyc in range(num_cyclists):
            interpolated_function = interp1d(time, raw_power_curves[cyc], kind = 'cubic')
            for col in range(0, num_bends_steady_state):
                for row in range(col + 1, num_bends_steady_state):
                    # Slight modification for first and last lap
                    if (col == 0) and (row == num_bends_steady_state - 1):
                        time_in_lead = num_bends_steady_state * half_lap_time + penalty_time
                    elif (col == 0) and (row != num_bends_steady_state - 1):
                        time_in_lead = ((row - col) + .5) * half_lap_time + (2 * penalty_time)
                    elif (col != 0) and (row != num_bends_steady_state - 1):
                        time_in_lead = (row - col) * half_lap_time + (2 * penalty_time)
                    elif (col != 0) and (row == num_bends_steady_state - 1):
                        time_in_lead = ((row - col) + .5) * half_lap_time + penalty_time
                    else:
                        print("Missed Case")

                    max_power[cyc][row][col] = max(interpolated_function(time_in_lead), critical_power[cyc])
                    for drag in range(len(drags)):
                        calculated_power = (.5*rho*CdA[cyc]*(velocity_m_per_sec**3)) * drags[drag]
                        if calculated_power <= max_power[cyc][row][col]:
                            power = max(0, calculated_power - critical_power[cyc])
                            work = power * time_in_lead
                            W_depleted[cyc][drag][row][col] = work
                        else:
                            W_depleted[cyc][drag][row][col] = 1000 * w_prime[cyc]
        return(W_depleted)


    # In[25]:


    def print_results(results_dictionary):
    # Print results in terms of laps
    # The array indexes translate to the following lap equivalents
    # [0: 0.25, 1: 0.75, 2: 1.25, 3: 1.75, 4: 2.25, 5: 2.75, 6: 3.25, 7: 3.75, 8: 4.25, 9: 4.75, 10: 5.25,
    #  11: 5.75, 12: 6.25, 13: 6.75, 14: 7.25, 15: 7.75, 16: 8.25, 17: 8.75, 18: 9.25, 19: 9.75, 20: 10.25,
    #  21: 10.75, 22: 11.25, 23: 11.75, 24: 12.25, 25: 12.75, 26: 13.25, 27: 13.75, 28: 14.25, 29: 14.75, 30: 15.25,
    #  31: 15.75
        cyclist_order = "Optimal cyclist order is: "
        for cyclist in range(num_cyclists):
            cyclist_order = cyclist_order + results_dictionary["cyclist_order"][cyclist] + ", "
        cyclist_order = cyclist_order[:-2]
        print(cyclist_order)
        print("")

        strategy = str(results_dictionary["number_of_intervals"]) + " intervals. Switch leaders at laps: " + str(results_dictionary["switch_strategy"])
        n = results_dictionary["number_of_intervals"]
        print(strategy)
        print("")
        print("Team work depletion: " + str(round(results_dictionary["team_work_depletion"], 2)) + " W, " + str(round(results_dictionary["team_work_depletion_percentage"], 2)) + "%")
        for cyclist in range(num_cyclists):
            print("Cyclist " + results_dictionary["cyclist_order"][cyclist] + " depleted " + str(round(results_dictionary["cyclist_work_depletion"][cyclist],2)) + " W, " + str(round(results_dictionary["cyclist_work_depletion_percent"][cyclist], 2)) + "% of their W'")

        if (sum(results_dictionary["cyclist_work_depletion"])) == results_dictionary["team_work_depletion"]:
            print("Sum of individual cyclists power equals objective function value")
        else:
            print("Objective Function - sum of individual cyclists work depleted equals " + str(results_dictionary["team_work_depletion"] - sum(results_dictionary["cyclist_work_depletion"])))
        print("")
        print("Expected split time per lap: " + str(results_dictionary["half_lap_time"] * 2) + " (s)")
        print("Expected constant velocity: " + str(round(results_dictionary["velocity_km_per_hour"],2)) + " km/hr")




    # In[26]:


    def generate_infeasible_sol_results_dictionary(n, permutation_to_alpha, half_lap_time, velocity_m_per_sec):
        results_dictionary = {}
        results_dictionary["cyclist_order"] = permutation_to_alpha
        results_dictionary["number_of_intervals"] = n
        results_dictionary["switch_strategy"] = {0: -1}
        results_dictionary["team_work_depletion"] = -1
        results_dictionary["team_work_depletion_percentage"] = -1
        results_dictionary["cyclist_work_depletion"] = [-1, -1, -1, -1]
        results_dictionary["cyclist_work_depletion_percent"] = [-1, -1, -1, -1]
        results_dictionary["half_lap_time"] = half_lap_time
        results_dictionary["velocity_km_per_hour"] = velocity_m_per_sec * 3.6
        results_dictionary["feasibility"] = 'infeasible'

        return(results_dictionary)


    # In[32]:


    # n is number of switches
    def find_optimal_solution(n, permutation_to_alpha, half_lap_time, velocity_m_per_sec, critical_power, w_prime, CdA, m, raw_power_curves, num_half_laps_to_accel, enforce_first_switch_half_lap, velocity_km_per_hour):
        W_depleted = initialize_W_depleted_matrix(half_lap_time, velocity_m_per_sec, critical_power, w_prime, CdA, raw_power_curves, num_half_laps_to_accel)
        num_bends_steady_state = num_bends - num_half_laps_to_accel
        time_to_accel = (2 * 125 * num_half_laps_to_accel) / velocity_m_per_sec
        results_dictionary = {}
        results_dictionary["num_half_laps_to_accel"] = num_half_laps_to_accel

        # Create the model object
        model= gp.Model ("AusCycling_Model")

        # Add the decision variables
        z = model.addVars(num_bends_steady_state, num_bends_steady_state, n, vtype=GRB.BINARY, name="z")

        # Constraints
        ### Maximum work per cyclist constraint (Need to review this constraint)
        for cyclist in range(num_cyclists):
            work_from_acceleration = drags[cyclist] * ((1 / 2) * m[cyclist] * (velocity_m_per_sec**2))
            max_work_constraint = model.addConstr(work_from_acceleration + (sum(z[i, j, k] * W_depleted[cyclist, ((cyclists_init_order[cyclist] + (4 - (k % 4))) % 4), i, j] for i in range(num_bends_steady_state) for j in range(num_bends_steady_state) for k in range(n))) <= w_prime[cyclist], name="max_work")

        ### Number of intervals constraint
        number_intervals = model.addConstr(sum(z[i, j, k] for i in range(num_bends_steady_state) for j in range(num_bends_steady_state) for k in range(n)) == n, name="number_intervals")

        ### Number of switches per interval constraint
        for k in range(n):
            number_switches_per_interval = model.addConstr(sum(z[i, j, k] for i in range(num_bends_steady_state) for j in range(num_bends_steady_state)) == 1, name="number_switches_in_interval_" + str(k))

        initial_switch = enforce_first_switch_half_lap - num_half_laps_to_accel
        first_switch = model.addConstr((z[initial_switch,0,0] == 1), name="enforce switch after acceleration")
        interval_end = model.addConstr((sum(z[num_bends_steady_state-1,j,n-1] for j in range(num_bends_steady_state)) == 1), name="interval_end")

        ### Intervals start and end from an “Active Bend”
        for s in range(n-1):
            intervals_start_end = model.addConstrs(((sum(z[i, k, s + 1] for i in range(num_bends_steady_state)) == sum(z[k, j, s] for j in range(num_bends_steady_state))) for k in range(num_bends_steady_state)), name="intervals_start_end")

        # Intervals must have bends that go in order
        for col in range(1, num_bends_steady_state):
            in_order_bends_first_row_0 = model.addConstr(z[0, col, 0] == 0, name="in_order_bends")
        for s in range(1,n):
            for col in range(num_bends_steady_state):
                in_order_bends_first_row_other_n = model.addConstr(z[0, col, s] == 0, name="in_order_bends")
        for s in range(n):
            for row in range(1, num_bends_steady_state):
                for col in range(row, num_bends_steady_state):
                    in_order_bends = model.addConstr(z[row, col, s] == 0, name="in_order_bends")

        # Objective Function
        total_work_tracker = [0, 0, 0, 0]
        for cyclist in range(num_cyclists):
            work_from_acceleration = drags[cyclist] * ((1 / 2) * m[cyclist] * (velocity_m_per_sec**2))
            #work_from_acceleration = 0
            total_work_tracker[cyclist] = work_from_acceleration + (sum(z[i, j, k] * W_depleted[cyclist, ((cyclists_init_order[cyclist] + (4 - (k % 4))) % 4), i, j] for i in range(num_bends_steady_state) for j in range(num_bends_steady_state) for k in range(n)))
        total_work = sum(total_work_tracker)
        objective_function = model.setObjective(total_work, GRB.MAXIMIZE)
        # suppress output
        model.setParam('OutputFlag', 0)

        model.optimize()

        status = model.status
        if status == gp.GRB.Status.INFEASIBLE:
            print("Model is infeasible, moving on to the next model...")
            results_dictionary = generate_infeasible_sol_results_dictionary(n, permutation_to_alpha, half_lap_time, velocity_m_per_sec)
            # Move on to the next iteration of the loop
            #continue
        else:
            results_dictionary["cyclist_order"] = permutation_to_alpha
            results_dictionary["number_of_intervals"] = n
            results_dictionary["team_work_depletion"] = model.ObjVal
            results_dictionary["team_work_depletion_percentage"] = model.ObjVal / team_w_prime * 100
            results_dictionary["switch_strategy"] = {}
            for k in range(n-1):
                for j in range(num_bends_steady_state):
                    for i in range(num_bends_steady_state):
                        # Retrieve the value of the decision variable at indices (i, j, k)
                        value = z[i, j, k].X
                        if value > 0.1:
                            results_dictionary["switch_strategy"][k] = (.5*i)+.25 + (num_half_laps_to_accel/2)
            total_work_output = [0, 0, 0, 0]
            total_work_output_percent = [0, 0, 0, 0]
            z_values = model.getAttr('X', z)

            #z_values[(i, j, k)]
            for cyclist in range(num_cyclists):
                work_from_acceleration = drags[cyclist] * ((1 / 2) * m[cyclist] * (velocity_m_per_sec**2))
                total_work_output[cyclist] = work_from_acceleration + sum(z_values[i, j, k] * W_depleted[cyclist, ((cyclists_init_order[cyclist] + (4 - (k % 4))) % 4), i, j] for i in range(num_bends_steady_state) for j in range(num_bends_steady_state) for k in range(n))
                total_work_output_percent[cyclist] = total_work_output[cyclist] / w_prime[cyclist] * 100
            results_dictionary["cyclist_work_depletion"] = total_work_output
            results_dictionary["cyclist_work_depletion_percent"] = total_work_output_percent
            results_dictionary["half_lap_time"] = half_lap_time
            results_dictionary["velocity_km_per_hour"] = velocity_km_per_hour
            results_dictionary["feasibility"] = 'feasible'

        return(results_dictionary)



    # Variables that may change
    
    csv_file_path = os.path.join(absolute_path, "results.csv")
    init_num_intervals = 7
    num_intervals_to_try = 3
    # half_lap_times = [6.65, 6.70, 6.75, 6.8, 6.85]
    half_lap_times = [6.7, 6.8]
    num_half_laps_to_accel = 3
    enforce_first_switch_lap = 4

    final_num_intervals = init_num_intervals + num_intervals_to_try
    optimal_team_work_depletion = 0
    optimal_number_of_intervals = 0
    optimal_strategy = generate_infeasible_sol_results_dictionary(init_num_intervals, ('A','B','C','D'), half_lap_times[0], 125/half_lap_times[0])
    optimal_time = 100
    
    #FINISH
    with open(csv_file_path, mode='w', newline='') as file:
        # find optimal cyclist order
        writer = csv.writer(file)
        column_titles = ['Permutation', 'Num_Intervals', 'Strategy', 'Team Work Depletion', 'Team Work Depletion %', 
                         'Cyclist init pos 0 Work Depleted', 'Cyclist init pos 0 Work Depleted %',
                         'Cyclist init pos 1 Work Depleted', 'Cyclist init pos 1 Work Depleted %',
                         'Cyclist init pos 2 Work Depleted', 'Cyclist init pos 2 Work Depleted %',
                         'Cyclist init pos 3 Work Depleted', 'Cyclist init pos 3 Work Depleted %',
                         'Expected Split Time per Lap', 'Expected Constant Velocity', 'Feasibility']
        writer.writerow(column_titles)
        for half_lap_time in reversed(half_lap_times):
            velocity_m_per_sec = half_lap_distance / half_lap_time
            velocity_km_per_hour = velocity_m_per_sec * 3.6
            for permutation in permutations(cyclists_init_order):
                critical_power = [0, 0, 0, 0]
                w_prime = [0, 0, 0, 0]
                CdA = [0, 0, 0, 0]
                m = [0, 0, 0, 0]
                raw_power_curves = [[],[],[],[]]
                for i in range(num_cyclists):
                    critical_power[i] = critical_power_from_csv[permutation[i]]
                    w_prime[i] = w_prime_from_csv[permutation[i]]
                    CdA[i] = CdA_from_csv[permutation[i]]
                    m[i] = m_from_csv[permutation[i]]
                    raw_power_curves[i] = raw_power_curves_from_csv[permutation[i]]    
       
                # find optimal number of intervals
                for num_intervals in range(init_num_intervals, final_num_intervals):
                    permutation_to_alpha = (rider_names[permutation[0]], rider_names[permutation[1]], rider_names[permutation[2]], rider_names[permutation[3]])
                    results_dictionary = find_optimal_solution(num_intervals, permutation_to_alpha, half_lap_time, velocity_m_per_sec, critical_power, w_prime, CdA, m, raw_power_curves, num_half_laps_to_accel, enforce_first_switch_lap, velocity_km_per_hour)
                    print("Testing permutation " + str(permutation_to_alpha) + " at " + str(num_intervals) + " intervals at " + str(half_lap_time) + " (s) half lap time.")
                    print("Team work depletion for " + str(num_intervals) + " intervals: " + str(results_dictionary["team_work_depletion"]))
                    strategy_dict = results_dictionary["switch_strategy"]
                    strategy = tuple(strategy_dict.values())
                    csv_data = [permutation_to_alpha, num_intervals, strategy, results_dictionary["team_work_depletion"], results_dictionary["team_work_depletion_percentage"],
                                results_dictionary["cyclist_work_depletion"][0], results_dictionary["cyclist_work_depletion_percent"][0],
                                results_dictionary["cyclist_work_depletion"][1], results_dictionary["cyclist_work_depletion_percent"][1],
                                results_dictionary["cyclist_work_depletion"][2], results_dictionary["cyclist_work_depletion_percent"][2],
                                results_dictionary["cyclist_work_depletion"][3], results_dictionary["cyclist_work_depletion_percent"][3],
                                results_dictionary["half_lap_time"]* 2, results_dictionary["velocity_km_per_hour"], results_dictionary["feasibility"]]
                    writer.writerow(csv_data)
                    if results_dictionary["feasibility"] == "feasible" and (half_lap_time < optimal_time or results_dictionary["team_work_depletion"] < optimal_team_work_depletion):
                        optimal_team_work_depletion = results_dictionary["team_work_depletion"]
                        optimal_number_of_intervals = num_intervals
                        optimal_time = half_lap_time
                        optimal_strategy = results_dictionary
    return optimal_strategy


# In[42]:


# print_results(run())


# In[ ]:




