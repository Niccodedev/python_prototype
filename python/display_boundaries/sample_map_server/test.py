#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import arguments
import json

from flask import Flask
# from flask import render_template
# from flask import request
from flask import Response
# from flask_compress import Compress
# from flask_cors import CORS, cross_origin

app = Flask(__name__)
# cors = CORS(app)
# app.config['CORS_HEADERS'] = 'Content-Type'
# Compress(app)

@app.route("/")
def test():
    test_output = dict()
    test_output["greeting"] = "Hello World!"

    return Response(json.dumps(test_output), mimetype='application/json')


if __name__ == '__main__':
    app.run()
