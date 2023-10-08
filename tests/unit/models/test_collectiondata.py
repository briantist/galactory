# -*- coding: utf-8 -*-
# (c) 2023 Brian Scholer (@briantist)

import sys
import pytest

import semver
from datetime import datetime, timedelta, timezone
from pytest_mock import MockFixture

from artifactory import ArtifactoryPath

from galactory.models import CollectionData


@pytest.mark.parametrize('collection_info', [{}])
@pytest.mark.parametrize('created_datetime', [datetime.now(timezone.utc)])
@pytest.mark.parametrize('modified_datetime', [datetime.now(timezone.utc)])
@pytest.mark.parametrize('filename', ['fake-file'])
@pytest.mark.parametrize('mime_type', ['fake-mime'])
@pytest.mark.parametrize('name', ['collection_name'])
@pytest.mark.parametrize('namespace', ['a_namespace'])
@pytest.mark.parametrize('sha256', ['m-m-m-my-sha-'])
@pytest.mark.parametrize('size', [-1, 0, 1])
@pytest.mark.parametrize('version', ['invalid', '1.2.3', '1.2.3-dev0'])
def test_collectiondata_init(
    collection_info,
    created_datetime,
    modified_datetime,
    filename,
    mime_type,
    name,
    namespace,
    sha256,
    size,
    version,
):
    data = CollectionData(
        collection_info=collection_info,
        created_datetime=created_datetime,
        modified_datetime=modified_datetime,
        filename=filename,
        mime_type=mime_type,
        name=name,
        namespace=namespace,
        sha256=sha256,
        size=size,
        version=version,
    )

    assert isinstance(data, CollectionData)
    assert data.created_datetime.utcoffset() == timedelta(0)
    assert data.modified_datetime.utcoffset() == timedelta(0)
    assert datetime.fromisoformat(data.created) == data.created_datetime
    assert datetime.fromisoformat(data.modified) == data.modified_datetime
    assert data.fqcn == f"{data.namespace}.{data.name}"
    assert data.version == version
    try:
        ver = semver.VersionInfo.parse(version)
    except ValueError:
        with pytest.raises(ValueError, match=rf"^{version} is not valid SemVer string"):
            _ = data.semver
    else:
        assert isinstance(data.semver, semver.VersionInfo)
        assert semver.VersionInfo.parse(data.version) == data.semver
        assert data.semver == ver


_COLLECTION_INFO = [
    ('fake', 'one', '0.1.0', 'A'),
    ('fake', 'one', '0.1.0', 'B'),
    ('fake', 'one', '0.1.0-dev0', 'A'),
    ('fake', 'two', '2.0.0', 'C'),
    ('jake', 'two', '2.0.0', 'D'),
]


@pytest.mark.parametrize(
    ('namespace1', 'name1', 'version1', 'sha256_1'),
    _COLLECTION_INFO,
)
@pytest.mark.parametrize(
    ('namespace2', 'name2', 'version2', 'sha256_2'),
    _COLLECTION_INFO,
)
def test_collectiondata_compare_collections(
    namespace1, name1, version1, sha256_1,
    namespace2, name2, version2, sha256_2,
):
    _common = dict(
        collection_info={},
        created_datetime=datetime.now(timezone.utc),
        modified_datetime=datetime.now(timezone.utc),
        filename='fname',
        mime_type='mime',
        size=0,
    )

    colA = CollectionData(namespace=namespace1, name=name1, version=version1, sha256=sha256_1, **_common)
    colB = CollectionData(namespace=namespace2, name=name2, version=version2, sha256=sha256_2, **_common)

    verA = semver.VersionInfo.parse(version1)
    verB = semver.VersionInfo.parse(version2)

    assert (colA == colB) == (sha256_1 == sha256_2)

    if colA != colB:
        if name1 != name2 or namespace1 != namespace2:
            assert (colA < colB) == False
        elif verA.prerelease is None == verB.prerelease is None:
            assert (colA < colB) == (verA < verB)
        else:
            assert (colA < colB) == (verA.prerelease is not None)


@pytest.mark.parametrize(
    ('namespace1', 'name1', 'version1', 'sha256_1'),
    _COLLECTION_INFO,
)
@pytest.mark.parametrize(
    'other_version',
    list(map(lambda x: x[2], _COLLECTION_INFO)),
)
def test_collectiondata_compare_versioninfo(
    namespace1, name1, version1, sha256_1,
    other_version,
):
    _common = dict(
        collection_info={},
        created_datetime=datetime.now(timezone.utc),
        modified_datetime=datetime.now(timezone.utc),
        filename='fname',
        mime_type='mime',
        size=0,
    )

    col = CollectionData(namespace=namespace1, name=name1, version=version1, sha256=sha256_1, **_common)

    ver = semver.VersionInfo.parse(other_version)

    assert (col == ver) == (col.semver == ver)
    if col.is_prerelease == (ver.prerelease is not None):
        assert (col < ver) == (col.semver < ver)
    else:
        assert (col < ver) == (col.is_prerelease)


def test_collectiondata_compare_othertypes(mocker: MockFixture, collection_data: CollectionData):
    spy_eq = mocker.spy(CollectionData, '__eq__')
    spy_lt = mocker.spy(CollectionData, '__lt__')

    standin = 5

    assert collection_data != mocker.sentinel.whatever
    spy_eq.assert_called_once_with(collection_data, mocker.sentinel.whatever)
    assert spy_eq.spy_return is NotImplemented
    spy_eq.reset_mock()

    assert collection_data != standin
    spy_eq.assert_called_once_with(collection_data, standin)
    assert spy_eq.spy_return is NotImplemented
    spy_eq.reset_mock()

    assert standin != collection_data
    spy_eq.assert_called_once_with(collection_data, standin)
    assert spy_eq.spy_return is NotImplemented
    spy_eq.reset_mock()

    rmsg = r"not supported between instances of 'CollectionData' and"

    with pytest.raises(TypeError, match=rmsg):
        assert not (collection_data < standin)
    spy_lt.assert_called_once_with(collection_data, standin)
    assert spy_lt.spy_return is NotImplemented
    spy_lt.reset_mock()

    with pytest.raises(TypeError, match=rmsg):
        assert not (collection_data > standin)
    spy_lt.assert_called_once_with(collection_data, standin)
    assert spy_lt.spy_return is NotImplemented
    spy_lt.reset_mock()


@pytest.mark.xfail(condition=(sys.version_info >= (3, 10)), reason="Python>=3.10 tests don't work: https://github.com/briantist/galactory/issues/90")
def test_from_artifactory_repository(mocker: MockFixture, repository: ArtifactoryPath):
    spy = mocker.spy(CollectionData, '__init__')

    col = None
    for item in repository.iterdir():
        if item.is_dir():
            continue
        if item.name.endswith('.tar.gz'):
            props = item.properties
            stat = item.stat()
            col = CollectionData.from_artifactory_path(path=item, properties=props, stat=stat)
            spy.assert_called_once()
            spy.reset_mock()

    assert col is not None, "Error, no collections found."
