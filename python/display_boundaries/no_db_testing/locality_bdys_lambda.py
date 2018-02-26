#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import arguments
import boto3
import gzip
import json
# import multiprocessing

import locality_bdys_display

from datetime import datetime

from flask import Flask
from flask import Response
from flask_compress import Compress
from flask_cors import CORS

# create Flask app
app = Flask(__name__)
CORS(app)
Compress(app)

# path to the GeoJSON files
file_path = "/Users/hugh.saalmans/tmp/locality_bdys_display_json"
# file_path = "/Users/hugh/tmp/locality_bdys_display_json"

# URL format for getting boundary data
GET_DATA_URL = "/<ml>/<mb>/<mr>/<mt>/"
# GET_DATA_URL = "/<ml>/<mb>/<mr>/<mt>/<z>/<t>/"

# e.g. https://859uppjni0.execute-api.ap-southeast-2.amazonaws.com/dev/151.0730838775635/-33.894428556111/151.2268924713135/-33.805610879310436/14/locality_bdys_display/

# http://127.0.0.1:5000/151.14/-33.85/151.15/-33.84/


@app.route(GET_DATA_URL)
def getbdys(ml, mb, mr, mt):
# def bdys(ml, mb, mr, mt, z, t):
    log = list()
    full_start_time = datetime.now()
    start_time = datetime.now()

    # # get bounding boxes acti
    # f = open("locality-bdys-display.json", 'r')
    # bounding_boxes = ast.literal_eval(f.read())
    # f.close()

    log.append("loaded bounding boxes in : {}".format(datetime.now() - start_time))
    start_time = datetime.now()

    # get map bounds as floats
    left = float(ml)
    bottom = float(mb)
    right = float(mr)
    top = float(mt)

    # filter boundaries by their bounding box
    # (note: this can result in the selection of bdys not within the requested area)
    bdy_ids = list()

    for bounding_box in locality_bdys_display.bounding_boxes:
        if (left <= bounding_box['l'] <= right and bottom <= bounding_box['b'] <= top or
            left <= bounding_box['l'] <= right and bottom <= bounding_box['t'] <= top or
            left <= bounding_box['r'] <= right and bottom <= bounding_box['t'] <= top or
            left <= bounding_box['r'] <= right and bottom <= bounding_box['b'] <= top):
                bdy_ids.append(bounding_box['id'])

    log.append("got boundary ids in : {}".format(datetime.now() - start_time))
    start_time = datetime.now()

    # get the GeoJSON records for each bdy
    output_dict = dict()
    output_dict["type"] = "FeatureCollection"

    feature_array = list()

    for bdy_id in bdy_ids:
        with gzip.GzipFile(file_path + "/" + bdy_id + ".gz", 'r') as fin:
            json_bytes = fin.read()

            json_str = json_bytes.decode('utf-8')
            feature_array.append(json_str)

        # bdy_file = open(file_path + "/" + bdy_id + ".json", "r")
        # feature_array.append(bdy_file.read())

    # Assemble the GeoJSON
    output_dict["features"] = feature_array

    log.append("json response constructed : {}".format(datetime.now() - start_time))
    print("{}\n\n{} records returned : {}".format("\n".join(log), len(bdy_ids), datetime.now() - full_start_time))

    return Response(json.dumps(output_dict), mimetype='application/json')


if __name__ == '__main__':
    app.run()
