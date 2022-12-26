# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

import pytest


@pytest.fixture(params=['/', ''])
def trailer(request):
    return lambda v: f"{v.rstrip('/')}{request.param}"
