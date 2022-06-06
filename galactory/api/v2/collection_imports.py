# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

from datetime import datetime
from flask import jsonify

from . import bp

@bp.route('/collection-imports/0')
@bp.route('/collection-imports/0/')
def import_singleton():
    out = {
        'state': 'completed',
        'finished_at': datetime.utcnow(),
    }
    return jsonify(out)
