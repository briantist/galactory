# -*- coding: utf-8 -*-
# (c) 2023 Brian Scholer (@briantist)

import pytest

import re
from semver import VersionInfo
from pytest_mock import MockFixture

from galactory.models import CollectionData, CollectionGroup


@pytest.mark.parametrize('name', ['collection_name', 'name2'])
@pytest.mark.parametrize('namespace', ['a_namespace', 'ns1'])
def test_collectiongroup_init(namespace, name):
    colgroup = CollectionGroup(namespace=namespace, name=name)

    assert isinstance(colgroup, CollectionGroup)
    assert colgroup.namespace == namespace
    assert colgroup.name == name
    assert colgroup.fqcn == f"{namespace}.{name}"
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
    spy.assert_called_once_with(colgroup, collection_data.semver, collection_data)
    assert len(colgroup) == 1
    assert colgroup.latest is collection_data


def test_collectiongroup_from_collection(mocker: MockFixture, collection_data: CollectionData):
    spy_init = mocker.spy(CollectionGroup, '__init__')
    spy_add = mocker.spy(CollectionGroup, 'add')
    colgroup = CollectionGroup.from_collection(collection_data)

    spy_init.assert_called_once_with(colgroup, namespace=collection_data.namespace, name=collection_data.name)
    spy_add.assert_called_once_with(colgroup, collection_data)
    assert len(colgroup) == 1
    assert colgroup.latest is collection_data


def test_collectiongroup_dunders(mocker: MockFixture, collection_data: CollectionData):
    colgroup = CollectionGroup.from_collection(collection_data)
    spy_get_key = mocker.spy(colgroup, '_get_key')

    assert colgroup[collection_data.semver] is collection_data
    spy_get_key.assert_called_once_with(collection_data.semver)
    spy_get_key.reset_mock()

    assert collection_data.version in colgroup
    spy_get_key.assert_called_once_with(collection_data.version, raises=False)
    spy_get_key.reset_mock()


def test_collectiongroup_delete(mocker: MockFixture, collection_data: CollectionData):
    spy_del = mocker.spy(CollectionGroup, '__delitem__')

    col1 = CollectionData.__new__(CollectionData)
    col2 = CollectionData.__new__(CollectionData)

    col1.__dict__.update(collection_data.__dict__.copy())
    col2.__dict__.update(collection_data.__dict__.copy())

    col1.version = '1.2.3'
    col1.sha256 = 'A'
    col2.version = '2.3.4'
    col2.sha256 = 'B'

    assert col1 is not col2
    assert col1 != col2
    assert col1 < col2
    assert col2 > col1

    colgroup = CollectionGroup.from_collection(col1)
    assert colgroup.latest is col1

    colgroup.add(col2)
    assert len(colgroup) == 2
    assert col1 in colgroup.values()
    assert col2 in colgroup.values()
    assert colgroup.latest is col2

    del(colgroup[col2.version])
    spy_del.assert_called_once_with(colgroup, col2.version)
    spy_del.reset_mock()
    assert colgroup.latest is col1

    del(colgroup[col1.semver])
    spy_del.assert_called_once_with(colgroup, col1.semver)
    assert colgroup.latest is None


@pytest.mark.parametrize('version', ['1.2.3-dev0', '2.3.4', '0.0.0-alpha'])
@pytest.mark.parametrize('as_vi', [True, False])
def test_collectiongroup_get_key_good_versions(version, as_vi):
    v = VersionInfo.parse(version)
    if as_vi:
        k = CollectionGroup._get_key(v)
        assert k is v
    else:
        k = CollectionGroup._get_key(version)
        assert k == v


@pytest.mark.parametrize('version', ['1.2.3dev0', 'now2.3.4', '0.0.0.0.0.0.0'])
def test_collectiongroup_get_key_bad_version_strings(version):
    with pytest.raises(ValueError, match=rf"^{version} is not valid SemVer string$"):
        CollectionGroup._get_key(version)


@pytest.mark.parametrize('version', [list(), tuple(), dict(), True, 2, 3.14159])
@pytest.mark.parametrize('raises', [True, False])
def test_collectiongroup_get_key_bad_version_types(version, raises):
    if raises:
        with pytest.raises(TypeError, match=r"Only valid semantic versions can be used as keys.$"):
            CollectionGroup._get_key(version, raises=raises)
    else:
        k = CollectionGroup._get_key(version, raises=raises)
        assert k is version
