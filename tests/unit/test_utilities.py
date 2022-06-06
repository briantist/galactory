# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

import pytest
from unittest import mock

from datetime import datetime, timedelta
from types import GeneratorType
import semver

from galactory.utilities import (
    discover_collections,
    collected_collections,
    load_manifest_from_artifactory,
    _collection_listing,
)


@pytest.fixture
def mock_load_manifest():
    def _load(repo):
        return repo._galactory_get_manifest()

    with mock.patch('galactory.utilities.load_manifest_from_artifactory', _load):
        yield _load


def test_discover_collections_any(repository, mock_load_manifest):
    gen = discover_collections(repository)

    assert isinstance(gen, GeneratorType)

    collections = list(gen)
    contents = list(repository)

    assert len(collections) == len(contents)

    for c in collections:
        # assert c['collection_info'] == mock_load_manifest(c)
        assert 'collection_info' in c
        assert datetime.fromisoformat(c['created']).utcoffset() == timedelta(0)
        assert datetime.fromisoformat(c['modified']).utcoffset() == timedelta(0)
        assert isinstance(c['namespace'], dict) and 'name' in c['namespace']
        assert 'name' in c
        assert c['fqcn'] == f"{c['namespace']['name']}.{c['name']}"
        assert 'filename' in c
        assert 'sha256' in c
        assert 'size' in c
        assert 'download_url' in c
        assert 'mime_type' in c
        assert 'version' in c
        assert isinstance(c['semver'], semver.VersionInfo) and semver.VersionInfo.parse(c['version']) == c['semver']


        # coldata = {
        #     'collection_info': manifest['collection_info'],
        #     'fqcn': props['fqcn'][0],
        #     'created': info.ctime.isoformat(),
        #     'modified': info.mtime.isoformat(),
        #     'namespace': {'name': props['namespace'][0]},
        #     'name': props['name'][0],
        #     'filename': p.name,
        #     'sha256': info.sha256,
        #     'size': info.size,
        #     'download_url': str(p),
        #     'mime_type': info.mime_type,
        #     'version': props['version'][0],
        #     'semver': semver.VersionInfo.parse(props['version'][0]),
        # }
