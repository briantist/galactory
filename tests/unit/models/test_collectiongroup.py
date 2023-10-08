# -*- coding: utf-8 -*-
# (c) 2023 Brian Scholer (@briantist)

import pytest

import re
from datetime import datetime, timezone
from pytest_mock import MockFixture

from galactory.models import CollectionData, CollectionGroup


@pytest.fixture
def collection_data() -> CollectionData:
    return CollectionData(
        collection_info={},
        namespace='ns',
        name='name',
        created_datetime=datetime.now(timezone.utc),
        modified_datetime=datetime.now(timezone.utc),
        filename='fake-file',
        mime_type='fake-file',
        sha256='m-m-m-my-sha-',
        size=0,
        version='0.0.0',
    )


@pytest.mark.parametrize('name', ['collection_name', 'name2'])
@pytest.mark.parametrize('namespace', ['a_namespace', 'ns1'])
def test_collectiongroup_init(namespace, name):
    colgroup = CollectionGroup(namespace=namespace, name=name)

    assert isinstance(colgroup, CollectionGroup)
    assert colgroup.namespace == namespace
    assert colgroup.name == name
    assert colgroup.latest is None
    assert len(colgroup) == len(colgroup.versions) == 0


@pytest.mark.parametrize('name', ['collection_name'])
@pytest.mark.parametrize('namespace', ['a_namespace'])
@pytest.mark.parametrize('version', [
    'abc.0',
    '0.hello',
    '99999.0.1111.6.4.3',
    None,
    4.4,
    True,
    [],
    {},
])
@pytest.mark.parametrize('value', [None, "thing", 2, 3.14159, False, [], {}])
def test_collectiongroup_bad_entries(mocker: MockFixture, namespace, name, collection_data, version, value):
    colgroup = CollectionGroup(namespace=namespace, name=name)

    # bad value type
    with pytest.raises(TypeError, match=r'^Values must be of type CollectionData\.$'):
        colgroup[version] = value

    # bad collection name
    with pytest.raises(ValueError, match=rf"^Attempted to add collection '{collection_data.namespace}.{collection_data.name}' to group for '{namespace}\.{name}'\.$"):
        colgroup[version] = collection_data

    # bad key (version)
    collection_data.namespace = namespace
    collection_data.name = name
    regver = re.escape(str(version))
    spy = mocker.spy(colgroup, '_get_key')
    with pytest.raises((TypeError, ValueError), match=rf"^(?:Only valid semantic versions can be used as keys\.|{regver} is not valid SemVer string)$"):
        colgroup[version] = collection_data

    spy.assert_called_once_with(version)


@pytest.mark.parametrize('name', ['collection_name'])
@pytest.mark.parametrize('namespace', ['a_namespace'])
def test_collectiongroup_add(mocker: MockFixture, namespace, name, collection_data):
    spy = mocker.spy(CollectionGroup, '__setitem__')
    colgroup = CollectionGroup(namespace=namespace, name=name)

    collection_data.namespace = namespace
    collection_data.name = name


    colgroup.add(collection_data)
    assert len(colgroup) == 1
    assert colgroup.latest is collection_data

    spy.assert_called_once_with(colgroup, collection_data.semver, collection_data)
