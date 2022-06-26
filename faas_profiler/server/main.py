#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask
from flask_marshmallow import Marshmallow

from .api import api
from .dashboard import dashboard

fp_server = Flask(__name__)
fp_server.register_blueprint(api, url_prefix='/api')
fp_server.register_blueprint(dashboard)

ma = Marshmallow(fp_server)

print(fp_server.url_map)
