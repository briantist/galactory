# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

from flask import Blueprint

bp = Blueprint('v1', __name__, url_prefix='/v1')
bp.get_send_file_max_age = lambda x: 0

from . import(
    health_checks,
)
