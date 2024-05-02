from flask import Flask, render_template, request
import csv
import io
from overwrite_csvs import overwrite

app = Flask(__name__)


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

    if file1 and file2:
        # Read the first CSV file
        stream1 = io.StringIO(file1.stream.read().decode("UTF8"), newline=None)
        csv_reader1 = csv.reader(stream1, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        data1 = next(csv_reader1)  # Read just the first row of the first file

        # Read the second CSV file
        stream2 = io.StringIO(file2.stream.read().decode("UTF8"), newline=None)
        csv_reader2 = csv.reader(stream2, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        data2 = next(csv_reader2)  # Read just the first row of the second file

        # You can process data1 and data2 here as per your requirement

        return render_template('output.html', data1=data1, data2=data2)


if __name__ == '__main__':
    app.run(debug=True)
