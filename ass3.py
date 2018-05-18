from flask import jsonify, Flask
from flask_restful import reqparse
from os import makedirs, remove
from os.path import dirname, exists, isfile, realpath
from pathlib import Path
from shutil import copyfile, rmtree
from subprocess import call
from requests import get, post
from xlrd import open_workbook, sheet
from zipfile import ZipFile
import csv

app = Flask(__name__)
resdir = dirname(realpath(__file__)) + "/resources/"

countrycode_fname = "Country-Code.xlsx"
tripadvisor_fname = "tripadvisor_in-restaurant_sample.csv"
zomato_fname = "zomato.csv"

country_code = {}

def read_file():
    def download_resources():
        kaggledir = str(Path.home()) + "/.kaggle/"
        if not exists(kaggledir):
            makedirs(kaggledir)
        copyfile(resdir + "kaggle.json", kaggledir + "kaggle.json")
        for i, fname in enumerate([countrycode_fname, zomato_fname, tripadvisor_fname]):
            if not isfile(resdir + fname):
                if i < 2:
                    kaggle_user = "shrutimehta/zomato-restaurants-data"
                else:
                    kaggle_user = "PromptCloudHQ/restaurants-on-tripadvisor"
                try:
                    call(["kaggle", "datasets", "download", "--force",\
                          "-d", kaggle_user,\
                          "-f", fname], shell=False)
                except OSError:
                    continue
                fname_new = fname if i < 1 else fname + ".zip"
                copyfile(kaggledir + "datasets/" + kaggle_user + "/" + fname_new,\
                         resdir + fname_new)
                zip_file = ZipFile(resdir + fname_new, 'r')
                zip_file.extractall(resdir)
                zip_file.close()
                for delete in ["_rels", "docProps", "xl"]:
                    if exists(resdir + delete):
                        rmtree(resdir + delete)
                for delete in ["[Content_Types].xml"]:
                    if isfile(resdir + delete):
                        remove(resdir + delete)

    download_resources()
    workbook = open_workbook(resdir + "Country-Code.xlsx")

    if len(workbook.sheet_names()) < 1:
        return

    sheet1 = workbook.sheets()[0]
    num_rows = sheet1.nrows
    for i in range(1,num_rows):
        row = sheet1.row(i)
        country_code[row[1].value] = int(row[0].value)

@app.route("/api/location", methods=['Get'])
def get_data_by_location():
    parser = reqparse.RequestParser()
    parser.add_argument('location', type=str)
    args = parser.parse_args()
    location = args.get("location")
    if location in country_code:
        loca_code = country_code[location]

    with open(resdir + tripadvisor_fname) as f:
        f_csv = csv.DictReader(f)
        for row in f_csv :
            if row['Country'] == location:
                print(row)

    if loca_code is None:
        return jsonify("ok"), 200

    with open(resdir + zomato_fname) as f1:
        fi_csv = csv.DictReader(f1)
        for each_row in fi_csv:
            if each_row['Country Code'] == loca_code:
                print(each_row)

    return jsonify("ok"), 200

if __name__ == '__main__':
    read_file()
    app.run()
