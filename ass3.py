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
googleplaces_api_baseurl = "https://maps.googleapis.com/maps/api/place/"

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

def get_googleplaces_key():
    if not isfile(resdir + "googleplaces.json"):
        return ""

    with open(resdir + "googleplaces.json", "r") as f:
        data = loads(f.read().replace("\n", "").strip())

    return data['key']

def googleplaces_rest_detail_extract(d_googleplaces):
    d = {}
    d["source"] = "googleplaces"
    take_key = ["formatted_address", "name", "place_id", "types", "url"]
    # maybe "formatted_phone_number"
    n_reviews = len(d_googleplaces["result"]["reviews"])\
            if "reviews" in d_googleplaces["result"].keys() else 0
    for key, val in d_googleplaces["result"].items():
        if key in take_key:
            if key == "formatted_address":
                d["address"] = val
            elif key == "place_id":
                d["id"] = val
            else:
                d[key] = val
    d["rating"] = {
        "aggregate_rating" : int(d_googleplaces["result"]["rating"]),
        "votes" : n_reviews
    }

    return d

def get_googleplaces_rests_by_lat_and_lon(lat, lon, reqargs):
    try:
        lat = float(lat)
    except ValueError:
        return {"message" : "googleplaces invalid latitude"}
    try:
        lon = float(lon)
    except ValueError:
        return {"message" : "googleplaces invalid longitude"}
    radius = 500 # in metres
    if 'radius' in reqargs.keys():
        try:
            radius = float(reqargs['radius'])
        except ValueError:
            pass # do nothing, assume default value
    url = googleplaces_api_baseurl +\
            "nearbysearch/json?key=" + get_googleplaces_key() +\
            "&location=" + str(lat) + "," + str(lon) + "&radius=" + str(radius) +\
            "&types=restaurant"
    req = get(url)
    res = loads(req.content)

    d = {}
    d["results_found"] = len(res["results"]) - 1
    d["restaurants"] = []
    for i in range(d["results_found"]):
        if i == 0:
            continue
        url = googleplaces_api_baseurl +\
            "details/json?key=" + get_googleplaces_key() +\
            "&placeid=" + res["results"][i]["place_id"]
        req = get(url)
        res1 = loads(req.content)
        d["restaurants"].append(googleplaces_rest_detail_extract(res1))

    return d

def get_zomato_key():
    if not isfile(resdir + "zomato.json"):
        return ""

    with open(resdir + "zomato.json", "r") as f:
        data = loads(f.read().replace("\n", "").strip())

    return data['user-key']

def get_zomato_search_result_params(d_zomato):
    d = {}

    start = 0
    if 'start' in d_zomato:
        try:
            start = int(d_zomato['start'])
        except ValueError:
            pass # do nothing, assume default value
    count = 20
    if 'count' in d_zomato:
        try:
            count = int(d_zomato['count'])
        except ValueError:
            pass # do nothing, assume default value
    pages = 1
    if 'pages' in d_zomato:
        try:
            pages = int(d_zomato['pages'])
        except ValueError:
            pass # do nothing, assume default value
    if "cuisines" in d_zomato:
        cuisines = list(set([c.strip()\
                for c in d_zomato["cuisines"].strip().lower().split(",")]))
        d["cuisines"] = cuisines

    d['start'] = start
    d['count'] = count
    d['pages'] = pages

    return d

def zomato_cuisine_names_to_ids(l_user, l_zomato):
    l = []
    for c in l_user:
        for c1 in l_zomato:
            if c == c1["cuisine"]["cuisine_name"].strip().lower():
                l.append(int(c1["cuisine"]["cuisine_id"]))
    l = map(str, l)

    return ",".join(l)

def zomato_rest_detail_extract(d_zomato, country_name, state_code):
    d = {}
    d["source"] = "zomato"
    take_key = ["id", "name", "url", "location", "cuisines", "user_rating"]
    # maybe "price_range"
    for key, val in d_zomato["restaurant"].items():
        if key in take_key:
            if key == "user_rating":
                val.pop("rating_text", None)
                val.pop("rating_color", None)
                d["rating"] = val
                for key1, val1 in d["rating"].items():
                    d["rating"][key1] = float(val1)
                continue
            elif key == "location":
                d["address"] = val["address"] + " " + state_code + " " +\
                        val["zipcode"] + ", " + country_name
                continue
            elif key == "cuisines":
                d["types"] = [v.strip() for v in val.strip().split(",")]
                continue
            d[key] = val

    return d

def get_zomato_rests_by_lat_and_lon(lat, lon, reqargs):
    try:
        lat = float(lat)
    except ValueError:
        return {"message" : "zomato invalid latitude"}
    try:
        lon = float(lon)
    except ValueError:
        return {"message" : "zomato invalid longitude"}
    d = get_zomato_search_result_params(reqargs)
    start = d['start']
    count = d['count']
    pages = d['pages']
    radius = 500 # in metres
    if 'radius' in reqargs.keys():
        try:
            radius = float(reqargs['radius'])
        except ValueError:
            pass # do nothing, assume default value
    headers = {
        "Content-Type" : "application/json",
        "user-key" : get_zomato_key()
    }

    url = zomato_api_baseurl + "cuisines?lat=" + str(lat) + "&lon=" + str(lon)
    req = get(url, headers=headers)
    res = loads(req.content)
    l_cuisines = zomato_cuisine_names_to_ids(d["cuisines"], res["cuisines"])\
            if "cuisines" in d.keys() else ""

    url = zomato_api_baseurl + "cities?lat=" + str(lat) + "&lon=" + str(lon)
    req = get(url, headers=headers)
    res1 = loads(req.content)
    country_name = None
    if len(res1["location_suggestions"]) != 0:
        country_name = res1["location_suggestions"][0]["country_name"]
        state_code = res1["location_suggestions"][0]["state_code"]
    assert country_name and state_code

    d = {}
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
            d["restaurants"].append(zomato_rest_detail_extract(rest, country_name, state_code))

    return d

@app.route("/restaurants/<string:lat>/<string:lon>", methods=['Get'])
def get_rests_by_lat_and_lon(lat, lon):
    d_api = {}
    for arg in request.args:
        d_api = request.args.get(arg)
    d_googleplaces = get_googleplaces_rests_by_lat_and_lon(lat, lon, d_api)
    d_zomato = get_zomato_rests_by_lat_and_lon(lat, lon, d_api)

    d = {}
    d["results_found"] = 0
    d["restaurants"] = []
    if "message" in d_googleplaces.keys():
        d["message"] = d_googleplaces["message"]
    else:
        d["results_found"] += d_googleplaces["results_found"]
        d["restaurants"] += d_googleplaces["restaurants"]
    if "message" in d_zomato.keys():
        d["message"] = d_zomato["message"]
    else:
        d["results_found"] += d_zomato["results_found"]
        d["restaurants"] += d_zomato["restaurants"]

    return dumps(d), 200

@app.route("/restaurants/<string:city>", methods=['Get'])
def get_zomato_rests_by_city(city):
    if not city:
        return dumps({"message" : "empty city name"}), 400

    city = city.strip().lower()
    d = get_zomato_search_result_params(request.args)
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

    d = {}
    d["results_found"] = 0
    d["restaurants"] = []
    for sug in res["location_suggestions"]:
        sug_id = sug["id"]
        sug_name = sug["name"]
        country_name = sug["country_name"]
        state_code = sug["state_code"]
        url = zomato_api_baseurl + "locations?query=" + sug_name
        req = get(url, headers=headers)
        res1 = loads(req.content)

        if len(res1["location_suggestions"]) < 1:
            continue

        url = zomato_api_baseurl + "cuisines?city_id=" + str(sug_id)
        req = get(url, headers=headers)
        res1 = loads(req.content)
        l_cuisines = zomato_cuisine_names_to_ids(d_cuisines, res1["cuisines"])\
                if d_cuisines else ""
        for i in range(pages):
            url = zomato_api_baseurl + "search?city_id=" + str(sug_id) +\
                    "&start=" + str(start + i * count) + "&count=" + str(count) +\
                    ("&cuisines=" + l_cuisines if l_cuisines else "")
            req = get(url, headers=headers)
            res1 = loads(req.content)

            d["results_found"] += len(res1["restaurants"])
            for rest in res1["restaurants"]:
                d["restaurants"].append(zomato_rest_detail_extract(rest, country_name,\
                                                                   state_code))

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
