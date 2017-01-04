
import asyncpg
import math
import uvloop

# from datetime import datetime
from sanic import Sanic
from sanic import response

loop = uvloop.new_event_loop()

app = Sanic()
app.debug = True

# Serve files from the static folder to the URL /static
app.static('/', './static')

async def initdb_pool():
    dbdict = {"database": "geo", "user": "postgres", "password": "password", "host": "localhost", "port": 5432}
    return await asyncpg.create_pool(**dbdict)


engine = loop.run_until_complete(initdb_pool())


@app.route("/")
async def test(request):
    return response.json({"test": True})


# http://127.0.0.1:8000/get-data/151.14/-33.85/151.15/-33.84/15/
# http://127.0.0.1:8000/get-data/151.10/-33.85/151.15/-33.80/14/

# LONGITUDE_PATTERN = "^[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$"
# LATITUDE_PATTERN = ""

GET_DATA_URL = "/get-data/<ml>/<mb>/<mr>/<mt>/<z>/"


@app.route(GET_DATA_URL)
async def get_data(request, ml, mb, mr, mt, z):
    # start_time = datetime.now()

    async with engine.acquire() as connection:

        zoom_level = int(z)

        # Set the number of decimal places for the output GeoJSON to reduce response size & speed up rendering
        decimal_places = await get_decimal_places(zoom_level)

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
        table_name = "address_counts_{0}".format(curr_width_name.replace("_0", ""), )
        schema_name = "hex"

        # sql = "SELECT x::text || y::text AS id, percent, difference, ST_AsGeoJSON(geom, $1) AS geometry " \
        #       "FROM $2.$3 " \
        #       "WHERE ST_Intersects(ST_SetSRID(ST_MakeBox2D(ST_Point($4, $5), ST_Point($6, $7)), 4326),geom)"
        sql = "SELECT x::text || y::text AS id, percent, difference, ST_AsGeoJSON(geom, {0}) AS geometry " \
              "FROM {1}.{2} " \
              "WHERE ST_Intersects(ST_SetSRID(ST_MakeBox2D(ST_Point({3}, {4}), ST_Point({5}, {6})), 4326),geom)" \
            .format(decimal_places, schema_name, table_name, ml, mb, mr, mt)

        # print(sql)

        async with connection.transaction():
            # query = await connection.prepare(sql)
            # result = await connection.fetchval(sql, decimal_places, schema_name, table_name, ml, mb, mr, mt)
            result = await connection.fetch(sql)

            # print(result)

            if not result:
                return response.json({'ok': False, 'error': 'No data returned'})
            else:
                # print("result is ", result)
                # print("Got data in : {0} seconds".format(datetime.now() - start_time))
                # start_time = datetime.now()

                geojson_result = await convert_to_geojson(result)
                # print("Converted to GeoJSON : {0} seconds".format(datetime.now() - start_time))

                return response.text(geojson_result)


async def convert_to_geojson(result):
    # output is the main content
    output = ['{"type":"FeatureCollection","features":[']
    i = 0

    # For each row returned...
    for record in result:
        # Make sure the geometry exists
        if record["geometry"] is not None:

            # If it's the first record, don't add a comma
            comma = "," if i > 0 else ""
            feature = [''.join([comma, '{"type":"Feature","geometry":', record["geometry"], ',"properties":{'])]

            j = 0
            # For each field returned, assemble the properties object
            for key, value in record.items():
                if key != 'geometry':
                    comma = "," if j > 0 else ""
                    feature.append(''.join([comma, '"', key, '":"', str(value), '"']))

                j += 1

            feature.append('}}')
            row_output = ''.join([item for item in feature])
            output.append(row_output)

        # start over
        i += 1

    output.append(']}')

    # Assemble the GeoJSON
    total_output = ''.join([item for item in output])

    return total_output


# maximum number of decimal places for GeoJSON and other JSON based formats (e.g. ArcGIS services)
async def get_decimal_places(zoom_level):
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, loop=loop, debug=True)
