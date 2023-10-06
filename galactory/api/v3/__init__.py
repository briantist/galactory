# -*- coding: utf-8 -*-
# (c) 2023 Brian Scholer (@briantist)

from flask import Blueprint

bp = Blueprint('v3', __name__, url_prefix='/v3')

from . import (
    # collection_imports,
    collections,
)
