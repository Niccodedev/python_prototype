#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import arguments
import boto3
import gzip
import json
# import multiprocessing

import locality_bdys_display

from botocore.config import Config
from datetime import datetime

from flask import Flask
from flask import Response
from flask_compress import Compress
from flask_cors import CORS

# create Flask app
app = Flask(__name__)
CORS(app)
Compress(app)

settings = dict()

# path to the GeoJSON files
# settings['file_path'] = "/Users/hugh.saalmans/tmp/locality_bdys_display_json"
# settings['file_path'] = "/Users/hugh/tmp/locality_bdys_display_json"

settings['aws_profile'] = "default"
settings['s3_bucket'] = "minus34.com"
settings['s3_path'] = "opendata/psma-201802/admin_bdys/locality-bdys-display"  # DO NOT put '/' at the start !

# URL format for getting boundary data
GET_DATA_URL = "/<ml>/<mb>/<mr>/<mt>/"

# http://127.0.0.1:5000/151.14/-33.85/151.15/-33.84/


@app.route(GET_DATA_URL)
def getbdys(ml, mb, mr, mt):
    log = list()
    full_start_time = datetime.now()
    # start_time = datetime.now()

    # get requested map bounds as floats
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

    # log.append("got boundary ids in : {}".format(datetime.now() - start_time))
    # start_time = datetime.now()

    # set source AWS connection
    # aws_session = boto3.Session(profile_name=settings["aws_profile"])
    # if 'proxy' in settings:
    #     s3_client = aws_session.client('s3', config=Config(proxies={'https': settings['proxy']}), verify=False)
    # else:
    s3_client = boto3.client('s3')

    # get the GeoJSON records for each bdy
    output_dict = dict()
    output_dict["type"] = "FeatureCollection"

    feature_array = list()

    for bdy_id in bdy_ids:
        file_path = "{}/{}.gz".format(settings['s3_path'], bdy_id)

        response = s3_client.get_object(Bucket=settings["s3_bucket"], Key=file_path)
        gzip_obj = response['Body'].read()
        json_str = json.loads(gzip.decompress(gzip_obj).decode('utf-8'))

        feature_array.append(json_str)

    # Assemble the GeoJSON
    output_dict["features"] = feature_array

    # log.append("json response constructed : {}".format(datetime.now() - start_time))
    print("{}\n\n{} records returned : {}".format("\n".join(log), len(bdy_ids), datetime.now() - full_start_time))

    return Response(json.dumps(output_dict), mimetype='application/json')


if __name__ == '__main__':
    app.run()
