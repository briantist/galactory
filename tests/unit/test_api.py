# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

from galactory import constants as C
from galactory.api import API_RESPONSE

from datetime import datetime

def test_api(client):
    response = client.get('/api/')
    data = response.json

    assert response.status_code == C.HTTP_OK
    assert data == API_RESPONSE
    assert 'v2' in data['available_versions']
    assert 'v2' == data['current_version']


def test_import_collection_status(client):
    response = client.get('/api/v2/collection-imports/0/')
    data = response.json

    assert response.status_code == C.HTTP_OK
    assert data['state'] == 'completed'
    assert datetime.fromisoformat(data['finished_at']).utcoffset() is None
