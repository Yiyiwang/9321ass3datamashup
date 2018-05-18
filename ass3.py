from flask import Flask
from flask_restful import reqparse
from flask import jsonify
import csv
import os,xlrd

app = Flask(__name__)
path=os.path.dirname(__file__)
country_code={}


def read_file():
    workbook = xlrd.open_workbook(path+"/Country-Code.xlsx")
    sheet1 = workbook.sheets()[0]
    num_rows = sheet1.nrows
    for i in range(1,num_rows):
        row = sheet1.row(i)
        #print(int(row[0].value),row[1].value)
        country_code[row[1].value] = int(row[0].value)
   # print(country_code)

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
    #print(location)
    if location in country_code:
        loca_code = country_code[location]
        #print(loca_code)
    if loca_code is None:
         with open(path+"/tripadvisor_in-restaurant_sample.csv") as f:
             f_csv = csv.DictReader(f)
             for row in f_csv :
                 if row['Country'] == location:
                     print(row)
    else:
         with open(path+"/tripadvisor_in-restaurant_sample.csv") as f, open(path+"/zomato.csv") as file:
             f_csv = csv.DictReader(f)
             for row in f_csv :
                 #print(row['Country'])
                 #print(row)
                 if row['Country'] == location:
                    print(row)
             fi_csv = csv.DictReader(file)
             for each_row in fi_csv:
                 if each_row['Country Code'] == loca_code:
                     print(each_row)

         return jsonify("ok"), 200



        

if __name__ == '__main__':
    read_file()
    app.run()
