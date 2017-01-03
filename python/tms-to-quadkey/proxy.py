
from flask import Flask
from flask import render_template
from flask import request
from flask import Response
# from flask.ext.compress import Compress

app = Flask(__name__, static_url_path='')
# Compress(app)


# Get the quadkey for a TMS map tile
@app.route("/get-bing-maps-tiles/")
def proxy():
    # start_time = datetime.now()

    # Get parameters from querystring
    map_left = request.args.get('ml')
    map_bottom = request.args.get('mb')
    map_right = request.args.get('mr')
    map_top = request.args.get('mt')
    zoom_level = int(request.args.get('z'))




def tile_to_quadkey(tile):
    index = ''

    # for z = tile[2]; z > 0; z--:
    for z in range(tile[2], 1, -1):
        b = 0
        mask = 1 << (z - 1)

        if tile[0] and mask != 0:
            b += 1
        if tile[1] and mask != 0:
            b += 2

        index += str(b)

    return index
