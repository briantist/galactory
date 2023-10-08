# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

import pytest
from galactory import constants as C

from datetime import datetime

@pytest.mark.parametrize('app', [
    dict(API_VERSION=['v2']),
    dict(API_VERSION=['v3']),
    dict(API_VERSION=['v3', 'v2']),
    None,
], indirect=True)
def test_api(app, client, trailer):
    response = client.get(trailer('/api'))
    data = response.json

    possible_versions = ('v2', 'v3')
    api_config = app.config.get('API_VERSION')
    active_versions = api_config or possible_versions

    assert response.status_code == C.HTTP_OK
    assert 'available_versions' in data

    if 'v2' in active_versions:
        assert data['current_version'] == 'v2'
    else:
        assert 'current_version' not in data

    for v in active_versions:
        assert v in possible_versions
        assert v in data['available_versions']
        assert data['available_versions'][v] == f"{v}/"


@pytest.mark.parametrize(['app', 'path'], [
    (dict(API_VERSION=['v2']), 'collection-imports/0'),
    (dict(API_VERSION=['v3']), 'imports/collections/0'),
], indirect=['app'])
def test_import_collection_status(app, path, client, trailer):
    active_version = app.config['API_VERSION'][0]
    response = client.get(trailer(f"/api/{active_version}/{path}"))
    data = response.json

    assert response.status_code == C.HTTP_OK
    assert data['state'] == 'completed'
    assert datetime.fromisoformat(data['finished_at']).utcoffset() is None
