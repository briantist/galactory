# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

from flask import Blueprint, jsonify

from .v1 import bp as v1

API_RESPONSE = {
    'available_versions': {
        'v1': 'v1/',
    },
    'current_version': 'v1',
    'description': 'Galactory Health Checks',
}

bp = Blueprint('health', __name__, url_prefix='/health')
bp.register_blueprint(v1)

@bp.route('')
@bp.route('/')
def health():
    return jsonify(API_RESPONSE)
