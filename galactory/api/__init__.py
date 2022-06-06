# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

from flask import Blueprint, jsonify

from .v2 import bp as v2

API_RESPONSE = {
    'available_versions': {
        'v2': 'v2/',
    },
    'current_version': 'v2',
    'description': 'GALAXY REST API',
}

bp = Blueprint('api', __name__, url_prefix='/api')
bp.register_blueprint(v2)


@bp.route('/')
def api():
    return jsonify(API_RESPONSE)
