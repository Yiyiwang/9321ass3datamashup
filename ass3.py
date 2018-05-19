from collection import OrderedDict
from flask import jsonify, Flask
from flask_restful import reqparse
from json import loads, dumps
from os import makedirs, remove
from os.path import dirname, exists, isfile, realpath
from pathlib import Path
from requests import get, post
from shutil import copyfile, rmtree
from subprocess import call
from xlrd import open_workbook, sheet
from zipfile import ZipFile
import csv

app = Flask(__name__)
resdir = dirname(realpath(__file__)) + "/resources/"

countrycode_fname = "Country-Code.xlsx"
tripadvisor_fname = "tripadvisor_in-restaurant_sample.csv"
zomato_fname = "zomato.csv"

zomato_api_baseurl = "https://developers.zomato.com/api/v2.1/"

country_code = {}

def read_file():
    def download_resources():
        # move kaggle api key to its appropriate location
        # or else kaggle won't work
        kaggledir = str(Path.home()) + "/.kaggle/"
        if not exists(kaggledir):
            makedirs(kaggledir)
        copyfile(resdir + "kaggle.json", kaggledir + "kaggle.json")

        # download any missing dataset
        for i, fname in enumerate([countrycode_fname, zomato_fname, tripadvisor_fname]):
            if not isfile(resdir + fname):
                # download datasets
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

                # move and unzip datasets
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
    workbook = open_workbook(resdir + countrycode_fname)
    if len(workbook.sheet_names()) < 1:
        return
    sheet1 = workbook.sheets()[0]
    num_rows = sheet1.nrows
    for i in range(1,num_rows):
        row = sheet1.row(i)
        country_code[row[1].value] = int(row[0].value)

def get_zomato_key():
    if not isfile(resdir + "zomato.json"):
        return ""

    with open(resdir + "zomato.json", "r") as f:
        data = loads(f.read().replace("\n", "").strip().lower())

    return data['user-key']

@app.route("/restaurants/<string:city>", methods=['Get'])
def get_zomato_rest_by_loc(city):
    if not city:
        return dumps({"message" : "empty city name"}), 400

    city = city.strip().lower()
    start = 0
    if 'start' in request.args:
        try:
            start = int(request.args.get('start'))
        except ValueError:
            pass # do nothing, assume default value
    count = 20
    if 'count' in request.args:
        try:
            count = int(request.args.get('count'))
        except ValueError:
            pass # do nothing, assume default value
    pages = 1
    if 'pages' in request.args:
        try:
            pages = int(request.args.get('pages'))
        except ValueError:
            pass # do nothing, assume default value
    headers = {
        "Content-Type" : "application/json",
        "user-key" : get_zomato_key()
    }
    url = zomato_api_baseurl + "cities?q=" + city
    req = get(url, headers)
    res = loads(req.content)

    if len(res["location_suggestions"]) < 1:
        return dumps({"message" : "city not found"}), 404

    d = OrderedDict()
    d["results_found"] = 0
    d["restaurants"] = []
    for sug in res["location_suggestions"]:
        sug_id = sug["id"]
        sug_name = sug["name"]
        url = zomato_api_baseurl + "locations?query=" + sug_name
        req = get(url, headers)
        res1 = loads(req.content)

        if len(res1["location_suggestions"]) < 1:
            continue

        entity_id = res1["location_suggestions"][0]["entity_id"]
        entity_type = res1["location_suggestions"][0]["entity_type"]

        for i in range(pages):
            url1 = zomato_api_baseurl + "search?entity_id=" + entity_id +\
                    "&entity_type=" + entity_type +\
                    "&start=" + str(start + i * count) + "&count=" + str(count)
            req1 = get(url1, headers)
            res2 = loads(req1.content)

            d["results_found"] += len(res2["restaurants"])
            for rest in res2["restaurants"]:
                d.append(rest)

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
