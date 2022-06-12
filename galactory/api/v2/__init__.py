# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

from flask import Blueprint

bp = Blueprint('v2', __name__, url_prefix='/v2')

from . import (
    collection_imports,
    collections,
)
