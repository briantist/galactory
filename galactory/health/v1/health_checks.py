# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

from datetime import datetime
from time import perf_counter
from flask import jsonify, g as ctx, current_app, url_for, request

from . import bp


@bp.before_request
def start_timer():
    ctx.start_time = perf_counter()


@bp.after_request
def commonize(response):
    elapsed_ms = int((perf_counter() - ctx.start_time) * 1000)

    scheme = current_app.config.get('PREFERRED_URL_SCHEME')
    custom_txt = current_app.config.get('HEALTH_CHECK_CUSTOM_TEXT', '')

    data = response.get_json()

    data['elapsed_ms'] = elapsed_ms
    data['response_time'] = datetime.utcnow()
    data['custom_text'] = custom_txt
    data['href'] = url_for(request.endpoint, _external=True, _scheme=scheme, **request.view_args)

    response.data = current_app.json.dumps(data)

    response.headers['Cache-Control'] = "no-cache, no-store, must-revalidate"
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    return response


@bp.route('/basic')
@bp.route('/basic/')
def basic():
    out = {
        'type': 'basic'
    }
    return jsonify(out)


#TODO: add more healthcheck types?
