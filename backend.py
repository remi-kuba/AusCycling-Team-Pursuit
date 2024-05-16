from flask import Flask, render_template, request
import pandas as pd
from gurobi_implementation.optimizer import run

app = Flask(__name__, static_url_path='/assets')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'physiology' not in request.files or 'power_curves' not in request.files:
        return "Both files are required"

    physiology = request.files['physiology']
    power_curves = request.files['power_curves']

    if physiology.filename == '' or power_curves.filename == '':
        return 'Both files are required'

    try:
        data1 = physiology, "gurobi_implementation/physiology.csv"
        data2 = power_curves, "gurobi_implementation/power_curve.csv"
        overwrite_files(data1, data2)

        # Results returned by gurobi
        # {
        #   'cyclist_order': ('x', 'x', 'x', 'x'),
        #   'number_of_intervals': #,
        #   'team_work_depletion': #.##,
        #   'team_work_depletion_percentage': #.##,
        #   'switch_strategy': {0: #.##,
        #                       1: #.##, ...},
        #   'cyclist_work_depletion': [#.##, #.##, #.##, #.##],
        #   'cyclist_work_depletion_percent': [#.##, #.##, #.##, #.##],
        #   'half_lap_time': #.#,
        #   'velocity_km_per_hour': #.##,
        #   'feasibility': 'feasible'/'infeasible',
        #   'num_half_laps_to_accel': #
        # }
        results = run()
        riders = [r for r in results["cyclist_order"]]
        velocity_m_s = results["velocity_km_per_hour"] / 3.6
        half_lap_time = round(125/velocity_m_s, 2)
        # velocity = results["velocity"]

        acc_distance = results["num_half_laps_to_accel"] * 125
        acceleration_time = acc_distance*2/velocity_m_s  # Kinematic equation
        constant_time = (4000 - acc_distance)/velocity_m_s
        expected_time = round(acceleration_time + constant_time, 2)

        num = 0
        bends = []
        while num in results["switch_strategy"]:
            bends.append(results["switch_strategy"][num])
            num += 1
        bends = [0] + bends + [16]
        switches = []
        for i in range(len(bends) - 1):
            distance = bends[i + 1] - bends[i]
            switches.append(distance)

        depletion = results["cyclist_work_depletion"]
        percent = results["cyclist_work_depletion_percent"]
        left = [d/p*100-d for d, p in zip(depletion, percent)]


    except Exception as e:
        return str(e)

    return render_template('output.html', velocity=round(velocity_m_s, 2), half_lap_time=half_lap_time,
                           expected_time=expected_time, riders=riders, depletion=depletion, left=left, percent=percent,
                           switches=switches)


def overwrite_files(*args):
    for (excel, csv_file) in args:
        df = pd.read_excel(excel)
        with open(csv_file, 'w') as file:
            df.to_csv(file, mode='w')


def generate_graphs():
    return None



if __name__ == '__main__':
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = -1
    app.run(debug=True, port=8000)
