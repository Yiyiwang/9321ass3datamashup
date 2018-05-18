from flask import jsonify, Flask
from flask_restful import reqparse
from os.path import dirname, isfile, realpath
from xlrd import open_workbook, sheet
import csv

app = Flask(__name__)
resdir = dirname(realpath(__file__)) + "/resources/"
country_code = {}

def read_file():
    workbook = xlrd.open_workbook(resdir + "/Country-Code.xlsx")

    if len(workbook.sheet_names()) < 1:
        return

    sheet1 = workbook.sheets()[0]
    num_rows = sheet1.nrows
    for i in range(1,num_rows):
        row = sheet1.row(i)
        country_code[row[1].value] = int(row[0].value)

  #  with open(path+"/tripadvisor_in-restaurant_sample.csv") as f:
   #     f_csv = csv.DictReader(f)
    #    for row in f_csv :
     #       print(row)


@app.route("/api/location", methods=['Get'])
def get_data_by_location():
    parser = reqparse.RequestParser()
    parser.add_argument('location', type=str)
    args = parser.parse_args()
    location = args.get("location")
    if location in country_code:
        loca_code = country_code[location]

    with open(resdir + "/tripadvisor_in-restaurant_sample.csv") as f:
        f_csv = csv.DictReader(f)
        for row in f_csv :
            if row['Country'] == location:
                print(row)

    if loca_code is None:
        return jsonify("ok"), 200

    with open(resdir + "/zomato.csv") as f1:
        fi_csv = csv.DictReader(f1)
        for each_row in fi_csv:
            if each_row['Country Code'] == loca_code:
                print(each_row)

    return jsonify("ok"), 200

if __name__ == '__main__':
    read_file()
    app.run()
