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
        # Assume results come in a dict of dicts:
        #   {"switches": [_, _, _],
        #    "starting order": ["m1", "m2", "m4", "m3"]
        #    "riders": {"m1": [W', depleted, percentage], "m2": [...], ...}
        #    "velocity": _,
        #    "expected time": _,
        #   }
        results = run()
        # results = {
        #     "switches": [4.25, 6.25, 9.25, 11.35],
        #     "riders": {"A": [1299, 800], "B": [2456, 2130], "C": [2139, 2090], "D": [2910, 2710]},
        #     "starting order": ["A", "B", "C", "D"],
        #     "velocity": 17.4,
        #     "expected time": 245.2,
        # }
        # riders = list(results["riders"].keys())
        riders = [r for r in results["cyclist_order"]]
        velocity = round(results["velocity_km_per_hour"], 2)
        velocity_m_s = results["velocity_km_per_hour"] / 3.6
        # velocity = results["velocity"]

        acceleration_time = 1000/velocity_m_s  # Kinematic equation
        constant_time = 3500/velocity_m_s
        expected_time = round(acceleration_time + constant_time, 2)
        # bends = [2.25, 2.75, 6.75, 10.75, 12.25, 15.25]

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
        # depletion = [results["riders"][rider][1] for rider in riders]
        # left = [(results["riders"][rider][0] - results["riders"][rider][1]) for rider in riders]
        # percent = [(results["riders"][rider][1] / results["riders"][rider][0] * 100) for rider in riders]


    except Exception as e:
        return str(e)

    return render_template('output.html', velocity=velocity, expected_time=expected_time, riders=riders, depletion=depletion,
                           left=left, percent=percent, switches=switches)


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
