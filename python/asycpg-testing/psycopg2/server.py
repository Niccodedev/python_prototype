
import math
import os
import psycopg2

from flask import Flask
from flask import render_template
# from flask import request
from flask import Response
from flask_cors import CORS, cross_origin
from flask_compress import Compress

app = Flask(__name__, static_url_path='')
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
Compress(app)

# create postgres connect string
settings = dict()
settings['pg_host'] = os.getenv("PGHOST", "localhost")
settings['pg_port'] = os.getenv("PGPORT", 5432)
settings['pg_db'] = os.getenv("PGDATABASE", "geo")
settings['pg_user'] = os.getenv("PGUSER", "postgres")
settings['pg_password'] = os.getenv("PGPASSWORD", "password")
settings['pg_schema'] = "hex"

settings['pg_connect_string'] = "dbname='{0}' host='{1}' port='{2}' user='{3}' password='{4}'".format(
    settings['pg_db'], settings['pg_host'], settings['pg_port'], settings['pg_user'], settings['pg_password'])


@app.route("/")
def homepage():
    return render_template('index.html')

GET_DATA_URL = "/get-data/<ml>/<mb>/<mr>/<mt>/<z>/"


@app.route(GET_DATA_URL)
@cross_origin()
def bdys(ml, mb, mr, mt, z):
    # start_time = datetime.now()

    zoom_level = int(z)

    # # Get parameters from querystring
    # map_left = request.args.get('ml')
    # map_bottom = request.args.get('mb')
    # map_right = request.args.get('mr')
    # map_top = request.args.get('mt')
    # zoom_level = int(request.args.get('z'))

    # Try to connect to Postgres
    try:
        pg_conn = psycopg2.connect(settings['pg_connect_string'])
    except psycopg2.Error:
        return "Unable to connect to the database."

    pg_cur = pg_conn.cursor()

    # Set the number of decimal places for the output GeoJSON to reduce response size & speed up rendering
    decimal_places = get_decimal_places(zoom_level)

    # get hex width for the zoom level
    start_zoom_level = 13
    start_width = 0.3  # in km
    multiple = 2.0
    max_width = 200.0

    curr_width = start_width
    curr_zoom_level = start_zoom_level

    while zoom_level < curr_zoom_level:
        curr_width *= multiple

        if curr_width > max_width:
            curr_width /= multiple

        curr_zoom_level -= 1

    # Get table name
    curr_width_name = str(curr_width).replace(".", "_")
    table_name = 'address_counts_{0}'.format(curr_width_name.replace("_0", ""),)

    sql = "SELECT x::text || y::text AS id, percent, difference, ST_AsGeoJSON(geom, {0}) AS geometry " \
          "FROM {1}.{2} " \
          "WHERE ST_Intersects(ST_SetSRID(ST_MakeBox2D(ST_Point({3}, {4}), ST_Point({5}, {6})), 4326),geom)"\
        .format(decimal_places, settings['pg_schema'], table_name, ml, mb, mr, mt)

    try:
        pg_cur.execute(sql)
    except psycopg2.Error:
        return "I can't SELECT : " + sql

    # Retrieve the results of the query
    rows = pg_cur.fetchall()
    # row_count = pg_cur.rowcount

    # Get the column names returned
    col_names = [desc[0] for desc in pg_cur.description]

    # Find the index of the column that holds the geometry
    geom_index = col_names.index("geometry")

    # output is the main content, row_output is the content from each record returned
    output = ['{"type":"FeatureCollection","features":[']
    i = 0

    # For each row returned...
    while i < len(rows):
        # Make sure the geometry exists
        if rows[i][geom_index] is not None:
            # If it's the first record, don't add a comma
            comma = "," if i > 0 else ""
            feature = [''.join([comma, '{"type":"Feature","geometry":', rows[i][geom_index], ',"properties":{'])]

            j = 0
            # For each field returned, assemble the properties object
            while j < len(col_names):
                if col_names[j] != 'geometry':
                    comma = "," if j > 0 else ""
                    feature.append(''.join([comma, '"', col_names[j], '":"', str(rows[i][j]), '"']))

                j += 1

            feature.append('}}')
            row_output = ''.join([item for item in feature])
            output.append(row_output)

        # start over
        i += 1

    output.append(']}')

    # Assemble the GeoJSON
    total_output = ''.join([item for item in output])

    pg_cur.close()
    pg_conn.close()

    # end_time = datetime.now()
    # print "PostGIS : {0} records in {1}".format(row_count, end_time - start_time)

    # response = total_output.encode("zlib")

    return Response(total_output, mimetype='application/json')


# maximum number of decimal places for GeoJSON and other JSON based formats (e.g. ArcGIS services)
def get_decimal_places(zoom_level):

    # rough metres to degrees conversation, using spherical WGS84 datum radius for simplicity and speed
    metres2degrees = (2.0 * math.pi * 6378137.0) / 360.0

    # default Google/Bing map tile scales
    metres_per_pixel = 156543.03390625 / math.pow(2.0, float(zoom_level))

    # the tolerance for thinning data and limiting decimal places in GeoJSON responses
    degrees_per_pixel = metres_per_pixel / metres2degrees

    scale_string = "{:10.9f}".format(degrees_per_pixel).split(".")[1]
    places = 1

    trigger = "0"

    # find how many zero decimal places there are. e.g. 0.00001234 = 4 zeros
    for c in scale_string:
        if c == trigger:
            places += 1
        else:
            trigger = "don't do anything else"  # used to cleanly exit the loop

    return places


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
    # app.run(port=80)
