# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

from flask import Blueprint

from .v2 import bp as v2
from .v3 import bp as v3

API_RESPONSE = {
    'available_versions': {
        'v2': 'v2/',
        'v3': 'v3/',
    },
    'current_version': 'v2', # This field doesn't exist in the v3 output anyway.
    'description': 'GALAXY REST API',
}

bp = Blueprint('api', __name__, url_prefix='/api')
bp.register_blueprint(v2)
bp.register_blueprint(v3)

@bp.route('')
@bp.route('/')
def api():
    return API_RESPONSE
