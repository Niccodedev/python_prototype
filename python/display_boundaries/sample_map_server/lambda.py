#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import arguments
import argparse
import ast
import json
# import logging
import os
import psycopg2
import psycopg2.extras
import ssl
# import sys

from datetime import datetime

from flask import Flask
# from flask import render_template
from flask import request
from flask import Response
# from flask_compress import Compress
# from flask_cors import CORS, cross_origin

from psycopg2.extensions import AsIs

# create Flask app
app = Flask(__name__)
# cors = CORS(app)
# app.config['CORS_HEADERS'] = 'Content-Type'
# Compress(app)

# # PG settings for debugging AWS PG server from outside of AWS
# if 'SERVERTYPE' in os.environ and os.environ['SERVERTYPE'] == 'AWS Lambda':
#     json_data = open('zappa_settings.json')
#     env_vars = json.load(json_data)['dev']['environment_variables']
#     for key, val in env_vars.items():
#         os.environ[key] = val

settings = dict()

# create postgres connect string
settings['pg_host'] = os.getenv("PGHOST", "localhost")
settings['pg_port'] = os.getenv("PGPORT", 5432)
settings['pg_db'] = os.getenv("PGDB", "geo")
settings['pg_user'] = os.getenv("PGUSER", "postgres")
settings['pg_password'] = os.getenv("PGPASSWORD", "password")

settings['pg_connect_string'] = "dbname='{0}' host='{1}' port='{2}' user='{3}' password='{4}'".format(
    settings['pg_db'], settings['pg_host'], settings['pg_port'], settings['pg_user'], settings['pg_password'])

# target schema and tables
settings['pg_schema'] = os.getenv("PGSCHEMA", "test")
settings['pg_table'] = "vw_locality_bdys_display_full_res_display"

# connect to Postgres
pg_conn_good = False

try:
    pg_conn = psycopg2.connect(settings['pg_connect_string'])
    pg_conn.autocommit = True
    pg_cur = pg_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    pg_conn_good = True
except psycopg2.Error:
    pass

GET_DATA_URL = "/<ml>/<mb>/<mr>/<mt>/<z>/<t>"


@app.route(GET_DATA_URL)
# @cross_origin()
def bdys(ml, mb, mr, mt, z, t=settings['pg_table']):

    # abort if no PG connection
    if not pg_conn_good:
        return Response("Epic fail - Couldn't connect to Postgres server!", mimetype='text/plain')

    zoom_level = int(z)

    # Get parameters from querystring
    ml = request.args.get('ml')
    mb = request.args.get('mb')
    mr = request.args.get('mr')
    mt = request.args.get('mt')
    zoom_level = int(request.args.get('z'))

    if t is None:
        t = request.args.get('t')

    # print(t)

    display_zoom = str(zoom_level).zfill(2)

    # test_output = dict()
    # test_output["yo"] = "Hello World!"
    #
    # return Response(json.dumps(test_output), mimetype='application/json')

    # build SQL with SQL injection protection
    # yes, this is ridiculous - if someone can find a shorthand way of doing this then fire up the pull requests!
    sql_template = "SELECT bdy.id, bdy.name, bdy.state, geojson_%s AS geometry " \
                   "FROM {0}.%s AS bdy " \
                   "WHERE bdy.geom && ST_MakeEnvelope(%s, %s, %s, %s, 4283)"\
        .format(settings['pg_schema'])

    sql = pg_cur.mogrify(sql_template, (AsIs(display_zoom), AsIs(t), AsIs(ml), AsIs(mb), AsIs(mr), AsIs(mt)))

    try:
        pg_cur.execute(sql)
    except psycopg2.Error:
        return "I can't SELECT:<br/><br/>" + str(sql)

    # Retrieve the results of the query
    rows = pg_cur.fetchall()

    # Get the column names returned
    col_names = [desc[0] for desc in pg_cur.description]

    # print("Got records from Postgres in {0}".format(datetime.now() - start_time))
    # start_time = datetime.now()

    # output is the main content, row_output is the content from each record returned
    output_dict = dict()
    output_dict["type"] = "FeatureCollection"

    i = 0
    feature_array = list()

    # For each row returned...
    for row in rows:
        feature_dict = dict()
        feature_dict["type"] = "Feature"

        properties_dict = dict()

        # For each field returned, assemble the feature and properties dictionaries
        for col in col_names:
            if col == 'geometry':
                feature_dict["geometry"] = ast.literal_eval(str(row[col]))
            elif col == 'id':
                feature_dict["id"] = row[col]
            else:
                properties_dict[col] = row[col]

        feature_dict["properties"] = properties_dict

        feature_array.append(feature_dict)

        # start over
        i += 1

    # Assemble the GeoJSON
    output_dict["features"] = feature_array

    # print("Parsed records into JSON in {1}".format(i, datetime.now() - start_time))
    # print("get-data: returned {0} records  {1}".format(i, datetime.now() - full_start_time))

    return Response(json.dumps(output_dict), mimetype='application/json')


if __name__ == '__main__':
    # if args.d:
    #     app.run(host='0.0.0.0', port=8000, debug=True)
    # else:

    # run with Zappa
    app.run()

    # run over HTTP
    # app.run(host='0.0.0.0', port=8000, debug=True)

    # run over HTTPS
    # context = ('cert.crt', 'key.key')
    # app.run(host='0.0.0.0', port=8443, ssl_context=context, debug=True)
