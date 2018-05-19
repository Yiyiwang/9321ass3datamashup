from collections import OrderedDict
from flask import jsonify, Flask, request
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

def get_search_result_params(l):
    d = {}

    start = 0
    if 'start' in l:
        try:
            start = int(l.get('start'))
        except ValueError:
            pass # do nothing, assume default value
    count = 20
    if 'count' in l:
        try:
            count = int(l.get('count'))
        except ValueError:
            pass # do nothing, assume default value
    pages = 1
    if 'pages' in l:
        try:
            pages = int(l.get('pages'))
        except ValueError:
            pass # do nothing, assume default value
    if "cuisines" in l:
        cuisines = list(set([c.strip()\
                for c in l.get("cuisines").strip().lower().split(",")]))
        d["cuisines"] = cuisines

    d['start'] = start
    d['count'] = count
    d['pages'] = pages

    return d

def cuisine_names_to_ids(l_user, l_zomato):
    l = []
    for c in l_user:
        for c1 in l_zomato:
            if c == c1["cuisine"]["cuisine_name"].strip().lower():
                l.append(int(c1["cuisine"]["cuisine_id"]))
    l = map(str, l)

    return ",".join(l)

@app.route("/restaurants/<string:lat>/<string:lon>", methods=['Get'])
def get_zomato_rests_by_lat_and_lon(lat, lon):
    try:
        lat = float(lat)
    except ValueError:
        return dumps({"message" : "invalid latitude"}), 400
    try:
        lon = float(lon)
    except ValueError:
        return dumps({"message" : "invalid longitude"}), 400
    d = get_search_result_params(request.args)
    start = d['start']
    count = d['count']
    pages = d['pages']
    radius = 500 # in metres
    if 'radius' in request.args:
        try:
            radius = float(request.args.get('radius'))
        except ValueError:
            pass # do nothing, assume default value
    headers = {
        "Content-Type" : "application/json",
        "user-key" : get_zomato_key()
    }

    url = zomato_api_baseurl + "cuisines?lat=" + str(lat) + "&lon=" + str(lon)
    req = get(url, headers=headers)
    res = loads(req.content)
    l_cuisines = cuisine_names_to_ids(d["cuisines"], res["cuisines"])\
            if "cuisines" in d.keys() else ""
    d = OrderedDict()
    d["results_found"] = 0
    d["restaurants"] = []
    for i in range(pages):
        url = zomato_api_baseurl + "search?lat=" + str(lat) + "&lon=" + str(lon) +\
                "&radius=" + str(radius) + "&start=" + str(start + i * count) +\
                "&count=" + str(count) + ("&cuisines=" + l_cuisines if l_cuisines else "")
        req = get(url, headers=headers)
        res = loads(req.content)

        d["results_found"] += len(res["restaurants"])
        for rest in res["restaurants"]:
            d["restaurants"].append(rest)

    return dumps(d), 200

@app.route("/restaurants/<string:city>", methods=['Get'])
def get_zomato_rests_by_city(city):
    if not city:
        return dumps({"message" : "empty city name"}), 400

    city = city.strip().lower()
    d = get_search_result_params(request.args)
    start = d['start']
    count = d['count']
    pages = d['pages']
    d_cuisines = d["cuisines"] if "cuisines" in d.keys() else []
    headers = {
        "Content-Type" : "application/json",
        "user-key" : get_zomato_key()
    }
    url = zomato_api_baseurl + "cities?q=" + city
    req = get(url, headers=headers)
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
        req = get(url, headers=headers)
        res1 = loads(req.content)

        if len(res1["location_suggestions"]) < 1:
            continue

        entity_id = res1["location_suggestions"][0]["entity_id"]
        entity_type = res1["location_suggestions"][0]["entity_type"]
        city_id = int(res1["location_suggestions"][0]["city_id"])
        url = zomato_api_baseurl + "cuisines?city_id=" + str(city_id)
        req = get(url, headers=headers)
        res1 = loads(req.content)
        l_cuisines = cuisine_names_to_ids(d_cuisines, res1["cuisines"]) if d_cuisines\
                else ""
        for i in range(pages):
            url = zomato_api_baseurl + "search?entity_id=" + str(entity_id) +\
                    "&entity_type=" + entity_type +\
                    "&start=" + str(start + i * count) + "&count=" + str(count) +\
                    ("&cuisines=" + l_cuisines if l_cuisines else "")
            req = get(url, headers=headers)
            res1 = loads(req.content)

            d["results_found"] += len(res1["restaurants"])
            for rest in res1["restaurants"]:
                d["restaurants"].append(rest)

    return dumps(d), 200

@app.route("/api/location", methods=['Get'])
def get_data_by_location():
    parser = reqparse.RequestParser()
    parser.add_argument('location', type=str)
    args = parser.parse_args()
    location = args.get("location")
    loca_code = 0
    if location in country_code:
        loca_code = country_code[location]
    return_list=[]
    #open trpadvisor dataset and processing data
    with open(resdir + tripadvisor_fname) as f:
        f_csv = csv.DictReader(f)
        for row in f_csv :
            if row['Country'] == location:
                return_list.append(row)
    #return if there is no relate data in zomato dataset
    if loca_code == 0:
        return jsonify(return_list), 200
    #open zomato dataset and processing data
    try:
        with open(resdir + zomato_fname, 'r',encoding='ISO-8859-1') as f1:
            fi_csv = csv.DictReader(f1)
            for row in fi_csv:
                #print(loca_code,row['Country Code'])
                if int(row['Country Code']) == loca_code:
                    return_list.append(row)

        return jsonify(return_list), 200
    except IOError:
        pass

if __name__ == '__main__':
    read_file()
    app.run()
