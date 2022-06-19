# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

from flask import Blueprint

bp = Blueprint('download', __name__, url_prefix='/download')

from . import download
