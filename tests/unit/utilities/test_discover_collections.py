# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

import pytest
from unittest import mock

from datetime import datetime, timedelta
from types import GeneratorType
import semver

from galactory.utilities import discover_collections
from galactory.models import CollectionData


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
@pytest.mark.parametrize('collection', [None, 'whatever', 'hashi_vault', 'fake', 'devel'])
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
        assert isinstance(c, CollectionData)
        assert c.created_datetime.utcoffset() == timedelta(0)
        assert c.modified_datetime.utcoffset() == timedelta(0)
        assert datetime.fromisoformat(c.created) == c.created_datetime
        assert datetime.fromisoformat(c.modified) == c.modified_datetime
        assert c.fqcn == f"{c.namespace}.{c.name}"
        assert isinstance(c.semver, semver.VersionInfo)
        assert semver.VersionInfo.parse(c.version) == c.semver

        assert namespace is None or c.namespace == namespace
        assert collection is None or c.name == collection
        assert version is None or c.version == version
