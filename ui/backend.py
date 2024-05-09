from flask import Flask, render_template, request
import pandas as pd
from fake_impl.fake_gurobi import run

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
        data1 = physiology, "fake_impl/physiology.csv"
        data2 = power_curves, "fake_impl/power_curve.csv"
        overwrite_files(data1, data2)

        # Results returned by gurobi
        # Assume results come in a dict of dicts:
        #   {"switches": [_, _, _],
        #    "starting order": ["m1", "m2", "m4", "m3"]
        #    "riders": {"m1": [max_work, depleted, percentage], "m2": [...], ...}
        #    "velocity": _,
        #    "expected time": _,
        #   }
        results = run()
        dummy_results = {
            "switches": [4.25, 6.25, 9.25, 11.35],
            "riders": {"A": [1299, 800, 800/1299], "B": [2456,2130, 2130/2456], "C": [2139,2090,2090/2139], "D": [2910,2710,2710/2910]},
            "starting order": ["A", "B", "C", "D"],
            "velocity": 17.4,
            "expected time": 245.2,
        }
        data2 = ["m1", "m2", "m3", "m4"]
        data1 = [423, 412, 321, 293]
        riders = list(dummy_results["riders"].keys())
        depletion = [dummy_results["riders"][rider][1] for rider in riders]
        left = [(dummy_results["riders"][rider][0] - dummy_results["riders"][rider][1]) for rider in riders]
        percent = [(dummy_results["riders"][rider][2] * 100) for rider in riders]


    except Exception as e:
        return str(e)

    return render_template('output.html', data1=data1, data2=data2, riders=riders, depletion=depletion,
                           left=left, percent=percent)


def overwrite_files(*args):
    print(len(args))
    for (excel, csv_file) in args:
        df = pd.read_excel(excel)
        with open(csv_file, 'w') as file:
            df.to_csv(file, mode='w')


def generate_graphs():
    return None



if __name__ == '__main__':
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = -1
    app.run(debug=True, port=8000)
