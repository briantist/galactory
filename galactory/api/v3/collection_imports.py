# -*- coding: utf-8 -*-
# (c) 2023 Brian Scholer (@briantist)

from datetime import datetime

from . import bp

@bp.route('/imports/collections/0')
@bp.route('/imports/collections/0/', endpoint='import_singleton')
def import_singleton():
    out = {
        'state': 'completed',
        'finished_at': datetime.utcnow(),
    }
    return out
