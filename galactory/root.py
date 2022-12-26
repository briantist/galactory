# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

from flask import Blueprint, Response

bp = Blueprint('root', __name__, url_prefix='/')

@bp.route('')
@bp.route('/')
def index():
    return Response('Galactory is running', content_type='text/plain')
