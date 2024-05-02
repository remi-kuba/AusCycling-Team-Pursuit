from flask import Flask, render_template, request
import csv
import pandas as pd
import io

app = Flask(__name__, static_url_path='/assets')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'file1' not in request.files or 'file2' not in request.files:
        return "Both files are required"

    file1 = request.files['file1']
    file2 = request.files['file2']

    if file1.filename == '' or file2.filename == '':
        return 'Both files are required'

    try:
        data1 = get_first_row(file1)
        data2 = get_first_row(file2)
    except Exception as e:
        return str(e)

    return render_template('output.html', data1=data1, data2=data2)


def get_first_row(file):
    # stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    # csv_reader = csv.reader(stream, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    # first_row = []
    # for row in csv_reader:
    #     first_row.extend(row)
    # if first_row is None:
    #     raise ValueError("The CSV file is empty")
    df = pd.read_excel(file)
    rows = df.iloc[::]
    df.to_csv("../AusCycling_CP.csv")
    print(rows)
    html_content = rows.apply(generate_string, axis=1).tolist()
    print(html_content)
    return html_content


def generate_string(row):
    return f"""M1 {row["Time (s)"]}: {row["M1"]}"""



if __name__ == '__main__':
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = -1
    app.run(debug=True, port=8000)
