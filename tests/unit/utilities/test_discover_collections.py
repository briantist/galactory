# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

import pytest
from unittest import mock

from datetime import datetime, timedelta
from types import GeneratorType
import semver

from galactory.utilities import discover_collections


def test_discover_collections_skip_dirs(repository):
    with mock.patch('artifactory.ArtifactoryFileStat', mock.Mock(return_value=mock.Mock(is_dir=True, children=[]))):
        collections = list(discover_collections(repository))
        assert collections == []


@pytest.mark.parametrize('props', [{}, {'version': []}])
def test_discover_collections_skip_missing_version(repository, props):
    with mock.patch.object(repository.__class__, 'properties', property(mock.Mock(return_value=props))):
        collections = list(discover_collections(repository))
        assert collections == []


@pytest.mark.parametrize('namespace', [None, 'community', 'briantist', 'fake'])
@pytest.mark.parametrize('collection', [None, 'whatever', 'hashi_vault', 'fake'])
@pytest.mark.parametrize('version', [None, '2.5.0', '3.0.0', '0.1.0', '0.2.0', '0.0.0'])
def test_discover_collections_any(repository, manifest_loader, namespace, collection, version, app_request_context):
    gen = discover_collections(repository, namespace, collection, version)

    assert isinstance(gen, GeneratorType)

    collections = list(gen)
    contents = list(repository)

    assert len(collections) <= len(contents)
    if any([
        namespace == 'fake',
        collection == 'fake',
        version == '0.0.0',
    ]):
        assert len(collections) == 0

    # TODO: we're phasing out the manifest loader, remove later
    # assert len(contents) == manifest_loader.call_count
    # expected_calls = [mock.call(x) for x in contents]
    # manifest_loader.assert_has_calls(expected_calls, any_order=True)

    for c in collections:
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

        assert namespace is None or c['namespace']['name'] == namespace
        assert collection is None or c['name'] == collection
        assert version is None or c['semver'] == semver.VersionInfo.parse(version)

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
