#!/usr/bin/env python
# -*- coding: utf-8 -*-

# *********************************************************************************************************************
# create_display_boundaries.py
# *********************************************************************************************************************
#
# A script for creating thinned boundary tables in Postgres. This optimises them for web delivery & visualisation.
#
# Author: Hugh Saalmans, CL LocEng
#
# Process:
#   1. For each Postgres table in the input list - create a GeoJSON field for each tiled map zoom level
#
# *********************************************************************************************************************

import argparse
import logging
import display_boundary_utils as utils
import os
import psycopg2  # module needs to be installed
# import psycopg2.extensions
# import sys

from datetime import datetime


def main():
    start_time = datetime.now()

    # default message when running via command line
    parser = argparse.ArgumentParser(
        description='Creates boundary tables optimised for web visualisation')

    # # debugging? - sets database connection to localhost superuser if true
    # parser.add_argument('-d', action='store_true', default=False)

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

    # max parallel processes in Postgres (limit it to 3 to lay off L10-GEOSDI)
    settings['max_concurrent_processes'] = 3

    # set the zoom level that the geoms will be thinned to - for spatial querying only - NOT for display
    settings["default_zoom_level"] = 10

    # target schema and tables
    settings['input_schema'] = "admin_bdys_201705"
    settings['input_table_dicts'] = [
        {"table": "commonwealth_electorates", "id_field": "ce_pid", "name_field": "name", "state_field": "state"},
        {"table": "local_government_areas", "id_field": "lga_pid", "name_field": "name", "state_field": "state"},
        {"table": "local_government_wards", "id_field": "ward_pid", "name_field": "name", "state_field": "state"},
        {"table": "vw_locality_bdys_display_full_res", "id_field": "locality_pid", "name_field": "locality_name", "state_field": "state"},
        {"table": "state_bdys", "id_field": "state_pid", "name_field": "state", "state_field": "state"},
        {"table": "state_lower_house_electorates", "id_field": "se_lower_pid", "name_field": "name", "state_field": "state"},
        {"table": "state_upper_house_electorates", "id_field": "se_upper_pid", "name_field": "name", "state_field": "state"}]
        # {"table": "rf_psma_postcode_bdys", "id_field": "postcode", "name_field": "postcode", "state_field": "state"}]

    settings['output_schema'] = "test"
    settings['output_table_suffix'] = "display"

    # connect to Postgres
    try:
        pg_conn = psycopg2.connect(settings['pg_connect_string'])
        pg_conn.autocommit = True
        pg_cur = pg_conn.cursor()
        logger.debug("Connected to Postgres")
    except:
        message = "Unable to connect to database"
        logger.exception(message)
        return False

    # log PostGIS version
    utils.check_postgis_version(pg_cur, settings, logger)

    # Optimise boundaries for web visualisation
    success = create_display_boundaries(settings, settings['pg_user'])
    logger.info("Web optimised boundaries created : {0}".format(datetime.now() - start_time))

    pg_cur.close()
    pg_conn.close()
    logger.debug("Database connection closed")

    return success


def create_display_boundaries(settings, pg_user):

    # prepare boundaries for all tiled map zoom levels
    create_sql_list = list()
    insert_sql_list = list()
    vacuum_sql_list = list()

    for boundary_dict in settings['input_table_dicts']:
        input_pg_table = boundary_dict["table"]
        output_pg_table = "{0}_{1}".format(input_pg_table, settings["output_table_suffix"])

        id_field = boundary_dict["id_field"]
        name_field = boundary_dict["name_field"]
        state_field = boundary_dict["state_field"]

        # build create table statement
        create_table_list = list()
        create_table_list.append("DROP TABLE IF EXISTS {0}.{1} CASCADE;")
        create_table_list.append("CREATE TABLE {0}.{1} (")

        # build column list
        column_list = list()
        column_list.append("id text NOT NULL PRIMARY KEY")
        column_list.append("name text NOT NULL")
        column_list.append("state text NOT NULL")
        column_list.append("geom geometry(MultiPolygon, 4283) NULL")

        for zoom_level in range(4, 18):
            display_zoom = str(zoom_level).zfill(2)
            column_list.append("geojson_{0} jsonb NOT NULL".format(display_zoom))

        # add columns to create table statement and finish it
        create_table_list.append(",".join(column_list))
        create_table_list.append(") WITH (OIDS=FALSE);")
        create_table_list.append("ALTER TABLE {0}.{1} OWNER TO {2};")
        create_table_list.append("CREATE INDEX {1}_geom_idx ON {0}.{1} USING gist (geom);")
        create_table_list.append("ALTER TABLE {0}.{1} CLUSTER ON {1}_geom_idx;")
        create_table_list.append("COMMENT ON TABLE {0}.{1} IS "
                                 "'Optimised boundaries for web visualisation. Note: GDA94 lat/longs'")

        sql = "".join(create_table_list).format(settings['output_schema'], output_pg_table, pg_user)
        create_sql_list.append(sql)

        # build insert statement
        insert_into_list = list()
        insert_into_list.append("INSERT INTO {0}.{1}".format(settings['output_schema'], output_pg_table))
        insert_into_list.append("SELECT bdy.{0} AS id, bdy.{1} AS name, bdy.{2} AS state,"
                                .format(id_field, name_field, state_field))

        # thin geometry to the chosen zoom level to make spatial querying faster (not used for display)
        tolerance = utils.get_tolerance(settings["default_zoom_level"])
        insert_into_list.append("ST_Transform(ST_Multi(ST_Union(ST_MakeValid(ST_SimplifyVW("
                                "ST_Transform(bdy.geom, 3577), {0})))), 4283),".format(tolerance,))

        # create statements for geojson optimised for each zoom level
        geojson_list = list()

        for zoom_level in range(4, 18):
            # thin geometries to a default tolerance per zoom level
            tolerance = utils.get_tolerance(zoom_level)
            # trim coords to only the significant ones
            decimal_places = utils.get_decimal_places(zoom_level)

            geojson_list.append("ST_AsGeoJSON(ST_Transform(ST_Multi(ST_Union(ST_MakeValid(ST_SimplifyVW(ST_Transform("
                                "bdy.geom, 3577), {0})))), 4283), {1})::jsonb"
                                .format(tolerance, decimal_places))

        insert_into_list.append(",".join(geojson_list))
        insert_into_list.append("FROM {0}.{1} AS bdy".format(settings['input_schema'], input_pg_table))
        # insert_into_list.append("INNER JOIN {0}.{1}_{2} AS tab"
        #                         .format(settings['input_schema'], input_pg_table, pop_table))
        # insert_into_list.append("ON bdy.{0} = tab.{1}".format(id_field, settings["region_id_field"]))
        insert_into_list.append("WHERE bdy.geom IS NOT NULL")
        insert_into_list.append("GROUP BY {0}, {1}, {2}".format(id_field, name_field, state_field))

        sql = " ".join(insert_into_list)
        insert_sql_list.append(sql)

        vacuum_sql_list.append("VACUUM ANALYZE {0}.{1}".format(settings['output_schema'], output_pg_table))

    # print("\n".join(insert_sql_list))

    utils.multiprocess_list("sql", create_sql_list, settings, logger)
    utils.multiprocess_list("sql", insert_sql_list, settings, logger)
    
    # # remove duplicated fields in postcode and states
    # if name_field != id_field:
    # 
    # if state_field != name_field:

    utils.multiprocess_list("sql", vacuum_sql_list, settings, logger)

    return True


if __name__ == '__main__':
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

    logger.info("")
    logger.info("Start display boundary processing")
    utils.check_python_version(logger)

    if main():
        logger.info("Finished successfully!")
    else:
        logger.fatal("Something bad happened!")

    logger.info("")
    logger.info("-------------------------------------------------------------------------------")
