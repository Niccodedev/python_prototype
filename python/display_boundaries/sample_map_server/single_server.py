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
import ssl
# import sys

from datetime import datetime

from flask import Flask
from flask import render_template
# from flask import request
from flask import Response
from flask_compress import Compress
from flask_cors import CORS, cross_origin

from psycopg2.extensions import AsIs

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
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

# PG Options
parser.add_argument(
    '--pghost',
    help='Host name for Postgres server. Defaults to PGHOST environment variable if set, otherwise localhost.')
parser.add_argument(
    '--pgport', type=int,
    help='Port number for Postgres server. Defaults to PGPORT environment variable if set, otherwise 5432.')
parser.add_argument(
    '--pgdb',
    help='Database name for Postgres server. Defaults to PGDATABASE environment variable if set, '
         'otherwise geo.')
parser.add_argument(
    '--pguser',
    help='Username for Postgres server. Defaults to PGUSER environment variable if set, otherwise postgres.')
parser.add_argument(
    '--pgpassword',
    help='Password for Postgres server. Defaults to PGPASSWORD environment variable if set, '
         'otherwise \'password\'.')

args = parser.parse_args()

settings = dict()

# create postgres connect string
settings['pg_host'] = args.pghost or os.getenv("PGHOST", "localhost")
settings['pg_port'] = args.pgport or os.getenv("PGPORT", 5432)
settings['pg_db'] = args.pgdb or os.getenv("POSTGRES_USER", "geo")
settings['pg_user'] = args.pguser or os.getenv("POSTGRES_USER", "postgres")
settings['pg_password'] = args.pgpassword or os.getenv("POSTGRES_PASSWORD", "password")

settings['pg_connect_string'] = "dbname='{0}' host='{1}' port='{2}' user='{3}' password='{4}'".format(
    settings['pg_db'], settings['pg_host'], settings['pg_port'], settings['pg_user'], settings['pg_password'])

# target schema and tables
settings['input_schema'] = "test"
settings['default_table'] = "vw_locality_bdys_display_full_res"
settings['input_table_suffix'] = "display"

# connect to Postgres
pg_conn = psycopg2.connect(settings['pg_connect_string'])
pg_conn.autocommit = True
pg_cur = pg_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


# @app.route("/")
# @cross_origin()
# def homepage():
#     return render_template('index.html')

GET_DATA_URL = "/get-data/<ml>/<mb>/<mr>/<mt>/<z>/"


@app.route(GET_DATA_URL)
@cross_origin()
def bdys(ml, mb, mr, mt, z):
    # full_start_time = datetime.now()

    zoom_level = int(z)

    # # Get parameters from querystring
    # ml = request.args.get('ml')
    # mb = request.args.get('mb')
    # mr = request.args.get('mr')
    # mt = request.args.get('mt')
    # zoom_level = int(request.args.get('z'))

    # table_name = request.args.get('t')
    # # zoom_level = int(request.args.get('z'))
    #
    # print(table_name)

    # get the boundary table name from zoom level
    # if table_name is None:
    table_name = settings['default_table']

    table_name += "_"
    table_name += settings['input_table_suffix']

    display_zoom = str(zoom_level).zfill(2)

    test_output = dict()
    test_output["greeting"] = "Hello World!"

    return Response(json.dumps(test_output), mimetype='application/json')

    #
    # # build SQL with SQL injection protection
    # # yes, this is ridiculous - if someone can find a shorthand way of doing this then fire up the pull requests!
    # sql_template = "SELECT bdy.id, bdy.name, bdy.state, geojson_%s AS geometry " \
    #                "FROM {0}.%s AS bdy " \
    #                "WHERE bdy.geom && ST_MakeEnvelope(%s, %s, %s, %s, 4283)"\
    #     .format(settings['input_schema'])
    #
    # sql = pg_cur.mogrify(sql_template, (AsIs(display_zoom), AsIs(table_name),
    #                                     AsIs(ml), AsIs(mb), AsIs(mr), AsIs(mt)))
    #
    # try:
    #     pg_cur.execute(sql)
    # except psycopg2.Error:
    #     return "I can't SELECT:<br/><br/>" + str(sql)
    #
    # # Retrieve the results of the query
    # rows = pg_cur.fetchall()
    #
    # # Get the column names returned
    # col_names = [desc[0] for desc in pg_cur.description]
    #
    # # print("Got records from Postgres in {0}".format(datetime.now() - start_time))
    # # start_time = datetime.now()
    #
    # # output is the main content, row_output is the content from each record returned
    # output_dict = dict()
    # output_dict["type"] = "FeatureCollection"
    #
    # i = 0
    # feature_array = list()
    #
    # # For each row returned...
    # for row in rows:
    #     feature_dict = dict()
    #     feature_dict["type"] = "Feature"
    #
    #     properties_dict = dict()
    #
    #     # For each field returned, assemble the feature and properties dictionaries
    #     for col in col_names:
    #         if col == 'geometry':
    #             feature_dict["geometry"] = ast.literal_eval(str(row[col]))
    #         elif col == 'id':
    #             feature_dict["id"] = row[col]
    #         else:
    #             properties_dict[col] = row[col]
    #
    #     feature_dict["properties"] = properties_dict
    #
    #     feature_array.append(feature_dict)
    #
    #     # start over
    #     i += 1
    #
    # # Assemble the GeoJSON
    # output_dict["features"] = feature_array
    #
    # # print("Parsed records into JSON in {1}".format(i, datetime.now() - start_time))
    # # print("get-data: returned {0} records  {1}".format(i, datetime.now() - full_start_time))
    #
    # return Response(json.dumps(output_dict), mimetype='application/json')


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
