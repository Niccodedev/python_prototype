#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import arguments
import ast
import boto3
import gzip
import io
import json
import logging
import psycopg2
import psycopg2.extras
import os
import sys

from botocore.config import Config
from datetime import datetime

# get rid of annoying warnings due to the "man in the middle attack" proxy servers
import botocore.vendored.requests.packages.urllib3 as urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# keep Boto3 quiet unless something really bad happens
logging.getLogger('botocore').setLevel(logging.CRITICAL)
logging.getLogger('boto3').setLevel(logging.CRITICAL)

# add geo framework utilities
sys.path.append(os.environ['GIT_HOME'])  # point of entry to Git and home of passwords.ini file

from iagcl.geo_utilities.environment.interface import Interface_Suite
passwords, logger, heartbeat = Interface_Suite(log_file=None)

settings = dict()

# path to the GeoJSON files
# settings['file_path'] = "/Users/hugh.saalmans/tmp/locality_bdys_display_json"
# settings['file_path'] = "/Users/hugh/tmp/locality_bdys_display_json"

settings['aws_profile'] = "minus34"
settings['s3_bucket'] = "minus34.com"
settings['s3_path'] = "/opendata/psma-201802/admin_bdys/locality-bdys-display"

# settings['schema_name'] = "admin_bdys_201802"
# settings['tables_name'] = "locality_bdys_display"

settings['sql'] = "SELECT locality_pid AS id, locality_name AS name, postcode, state, " \
                  "ST_AsGeoJSON(geom, 5) AS geometry " \
                  "FROM admin_bdys_201802.locality_bdys_display"
# settings['sql'] = "SELECT locality_pid AS id, locality_name AS name, postcode, state, " \
#                   "ST_AsGeoJSON(geom, 5) AS geometry " \
#                   "FROM geo_adminbdys.aus_locality_boundaries_display"

# # set proxy
# settings['proxy'] = passwords.devproxies['https']

# create postgres connect string
settings['pg_host'] = os.getenv("PGHOST", "localhost")
settings['pg_port'] = os.getenv("PGPORT", 5432)
settings['pg_db'] = os.getenv("PGDB", "geo")
settings['pg_user'] = os.getenv("PGUSER", "postgres")
settings['pg_password'] = os.getenv("PGPASSWORD", "password")

settings['pg_connect_string'] = "dbname='{0}' host='{1}' port='{2}' user='{3}' password='{4}'".format(
    settings['pg_db'], settings['pg_host'], settings['pg_port'], settings['pg_user'], settings['pg_password'])

# connect to Postgres
pg_conn = psycopg2.connect(settings['pg_connect_string'])
# pg_conn.autocommit = True
pg_cur = pg_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def main():
    full_start_time = datetime.now()

    try:
        pg_cur.execute(settings['sql'])
    except psycopg2.Error:
        print("I can't SELECT:<br/><br/>" + settings['sql'])

    # Retrieve the results of the query
    rows = pg_cur.fetchall()

    # Get the column names returned
    col_names = [desc[0] for desc in pg_cur.description]

    # print("Got records from Postgres in {0}".format(datetime.now() - start_time))
    # start_time = datetime.now()

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

        json_str = json.dumps(feature_dict) + "\n"
        gz_file_obj = create_gzip_file_object(json_str)

        # json_bytes = json_str.encode('utf-8')
        #
        # with gzip.GzipFile(settings['file_path'] + "/" + feature_dict["id"] + ".gz", 'w') as f:
        #     f.write(json_bytes)

        file_path = "{}/{}.gz".format(settings['s3_path'], feature_dict["id"])

        # set target AWS connection
        aws_session = boto3.Session(profile_name=settings["aws_profile"])
        if 'proxy' in settings:
            s3_client = aws_session.client('s3', config=Config(proxies={'https': settings['proxy']}), verify=False)
        else:
            s3_client = aws_session.client('s3')

        # Upload the file to S3
        s3_client.upload_fileobj(gz_file_obj, settings["s3_bucket"], file_path)

        print("uploaded : {}".format(file_path))

    #     bdy_file = gzip.GzipFile(settings['file_path'] + "/" + feature_dict["id"] + ".json", mode="wb")
    #     bdy_file.write(str(feature_dict))
    #     # bdy_file = open(settings['file_path'] + "/" + feature_dict["id"] + ".json", "w")
    #     # bdy_file.write(str(feature_dict))
    #     bdy_file.close()

    print("Done! : {}".format(datetime.now() - full_start_time))


def create_gzip_file_object(string_):
    out = io.BytesIO()

    with gzip.GzipFile(fileobj=out, mode='w') as fo:
        fo.write(string_.encode('utf-8'))

    return out


if __name__ == '__main__':
    main()
