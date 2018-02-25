#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import arguments
import ast
# import json
import psycopg2
import psycopg2.extras
import os

settings = dict()

# path to the GeoJSON files
settings['file_path'] = "/Users/hugh.saalmans/tmp/locality_bdys_display_json"

# settings['schema_name'] = "admin_bdys_201802"
# settings['tables_name'] = "locality_bdys_display"
settings['sql'] = "SELECT locality_pid AS id, locality_name AS name, postcode, state, " \
                  "ST_AsGeoJSON(geom, 5) AS geometry " \
                  "FROM admin_bdys_201802.locality_bdys_display"

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

    try:
        pg_cur.execute(settings['sql'])
    except psycopg2.Error:
        return "I can't SELECT:<br/><br/>" + settings['sql']

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

        bdy_file = open(settings['file_path'] + "/" + feature_dict["id"] + ".json", "w")
        bdy_file.write(str(feature_dict))
        bdy_file.close()


if __name__ == '__main__':
    main()
