# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

from flask import Blueprint, Flask


def create_blueprint(app: Flask):
    api_version = app.config['API_VERSION']
    response = {
        'available_versions': {},
        'description': 'GALAXY REST API',
    }

    bp = Blueprint('api', __name__, url_prefix='/api')

    if api_version is None or 'v3' in api_version:
        app.logger.info(f"Registering Galaxy API v3")
        response['available_versions']['v3'] = 'v3/'
        from .v3 import bp as v3
        bp.register_blueprint(v3)

    if api_version is None or 'v2' in api_version:
        app.logger.info(f"Registering Galaxy API v2")
        response['available_versions']['v2'] = 'v2/'
        response['current_version'] = 'v2' # This field doesn't exist in the v3 output.
        from .v2 import bp as v2
        bp.register_blueprint(v2)

    @bp.route('')
    @bp.route('/', endpoint='api')
    def api():
        return response

    return bp
