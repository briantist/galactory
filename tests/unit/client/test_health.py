# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

import pytest

from galactory import constants as C
from galactory.health import API_RESPONSE

from datetime import datetime

from flask import current_app


def test_health_api(client, trailer):
    response = client.get(trailer('/health'))
    data = response.json

    assert response.status_code == C.HTTP_OK
    assert data == API_RESPONSE
    assert 'v1' in data['available_versions']
    assert 'v1' == data['current_version']


@pytest.mark.parametrize('custom', [None, '', 'test'])
def test_health_basic(client, trailer, custom, app_request_context):
    if custom is None:
        expected = ''
    else:
        current_app.config['HEALTH_CHECK_CUSTOM_TEXT'] = expected = custom

    response = client.get(trailer('/health/v1/basic'))
    data = response.json

    assert response.status_code == C.HTTP_OK
    assert data['type'] == 'basic'
    assert data['custom_text'] == expected
    assert isinstance(data['elapsed_ms'], int)
    assert datetime.fromisoformat(data['response_time']).utcoffset() is None
