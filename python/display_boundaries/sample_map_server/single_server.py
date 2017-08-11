#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import arguments
import argparse
import ast
import json
import logging
import os
import psycopg2
import psycopg2.extras
import sys

from datetime import datetime

from flask import Flask
from flask import render_template
from flask import request
from flask import Response
from flask_compress import Compress

from psycopg2.extensions import AsIs

app = Flask(__name__, static_url_path='')
Compress(app)

start_time = datetime.now()

logger = logging.getLogger()

# set logger
log_file = os.path.abspath(__file__).replace(".py", ".log")
logging.basicConfig(filename=log_file, level=logging.DEBUG, format="%(asctime)s %(message)s",
                    datefmt="%m/%d/%Y %I:%M:%S %p")

# setup logger to write to screen as well as writing to log file
# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)


# default message when running via command line
parser = argparse.ArgumentParser(
    description='Creates boundary tables optimised for web visualisation')

# debugging? - sets database connection to localhost superuser if true
parser.add_argument('-d', action='store_true', default=False)
args = parser.parse_args()



settings = dict()

# create postgres connect string
settings['pg_connect_string'] = "dbname={DB} host={HOST} port={PORT} user={USER} password={PASS}" \
    .format(**pg_settings)

# # max parallel processes in Postgres (limit it to 3 to lay off L10-GEOSDI)
# settings['max_concurrent_processes'] = 3
#
# # set the zoom level that the geoms will be thinned to - for spatial querying only - NOT for display
# settings["default_zoom_level"] = 10

# target schema and tables
settings['input_schema'] = "working_geo"
settings['default_table'] = "locality_bdys"
settings['input_table_suffix'] = "display"

# connect to Postgres
pg_conn = psycopg2.connect(settings['pg_connect_string'])
pg_conn.autocommit = True
pg_cur = pg_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


@app.route("/")
def homepage():
    return render_template('index.html')


@app.route("/get-data")
def get_data():
    full_start_time = datetime.now()
    # start_time = datetime.now()

    # Get parameters from querystring
    map_left = request.args.get('ml')
    map_bottom = request.args.get('mb')
    map_right = request.args.get('mr')
    map_top = request.args.get('mt')

    table_name = request.args.get('t')
    zoom_level = int(request.args.get('z'))

    # get the boundary table name from zoom level
    if table_name is None:
        table_name = settings['default_table']

    table_name += "_"
    table_name += settings['input_table_suffix']

    display_zoom = str(zoom_level).zfill(2)

    # build SQL with SQL injection protection
    # yes, this is ridiculous - if someone can find a shorthand way of doing this then fire up the pull requests!
    sql_template = "SELECT bdy.id, bdy.name, bdy.state, geojson_%s AS geometry " \
                   "FROM {0}.%s AS bdy " \
                   "WHERE bdy.geom && ST_MakeEnvelope(%s, %s, %s, %s, 4283)"\
        .format(settings['input_schema'])

    sql = pg_cur.mogrify(sql_template, (AsIs(display_zoom), AsIs(table_name),
                                        AsIs(map_left), AsIs(map_bottom), AsIs(map_right), AsIs(map_top)))

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
    print("get-data: returned {0} records  {1}".format(i, datetime.now() - full_start_time))

    return Response(json.dumps(output_dict), mimetype='application/json')


if __name__ == '__main__':
    if args.d:
        app.run(host='0.0.0.0', port=8081, debug=True)
    else:
        app.run(host='0.0.0.0', port=8081, debug=False)
