# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

from datetime import datetime
from flask import Flask, request
from flask.json import JSONEncoder
from .api import bp as api
from .download import bp as download


class DateTimeIsoFormatJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        return super().default(o)


def create_app(**config):
    app = Flask(__name__)
    app.json_encoder = DateTimeIsoFormatJSONEncoder
    app.config.update(**config)
    app.register_blueprint(api)
    app.register_blueprint(download)

    @app.before_request
    def log():
        if app.config.get('LOG_HEADERS'):
            app.logger.debug('Headers: %s', request.headers)

        if app.config.get('LOG_BODY'):
            app.logger.debug('Body: %s', request.get_data())

    return app
