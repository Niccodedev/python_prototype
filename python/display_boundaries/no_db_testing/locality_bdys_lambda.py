#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import arguments
import ast
import json
import os
import psycopg2
import psycopg2.extras

from datetime import datetime

from flask import Flask
from flask import Response
from flask_compress import Compress
from flask_cors import CORS, cross_origin

from psycopg2.extensions import AsIs

# create Flask app
app = Flask(__name__)
CORS(app)
Compress(app)

# URL format for getting boundary data
GET_DATA_URL = "/<ml>/<mb>/<mr>/<mt>/"
# GET_DATA_URL = "/<ml>/<mb>/<mr>/<mt>/<z>/<t>/"

# e.g. https://859uppjni0.execute-api.ap-southeast-2.amazonaws.com/dev/151.0730838775635/-33.894428556111/151.2268924713135/-33.805610879310436/14/locality_bdys_display/

# http://127.0.0.1:5000/151.14/-33.85/151.15/-33.84/

@app.route(GET_DATA_URL)
def bdys(ml, mb, mr, mt):
# def bdys(ml, mb, mr, mt, z, t):
    starttime = datetime.now()

    # get bounding boxes
    f = open("locality-bdys-display.json", 'r')
    bounding_boxes = ast.literal_eval(f.read())
    f.close()

    print("loaded bounding boxes in : {}".format(datetime.now() - starttime))

    # # get zoom level
    # zoom_level = int(z)
    # display_zoom = str(zom_level).zfill(2)

    # get map bounds as floats
    left = float(ml)
    bottom = float(mb)
    right = float(mr)
    top = float(mt)

    bdy_ids = list()

    # for bounding_box in bounding_boxes:


    return Response(json.dumps({"fred"}), mimetype='application/json')


if __name__ == '__main__':
    app.run()
