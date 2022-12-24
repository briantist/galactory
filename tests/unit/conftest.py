# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

import pytest
import json
import sys

from shutil import copytree
from artifactory import _ArtifactoryAccessor, _FakePathTemplate, ArtifactoryPath

from galactory import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def app_request_context(app):
    with app.app_context(), app.test_request_context():
        yield


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def virtual_fs_repo(fixture_finder, tmp_path):
    repo = tmp_path / 'repo'
    copytree(fixture_finder('artifactory', 'virtual'), repo)
    return repo


@pytest.fixture
def mock_artifactory_accessor(fixture_loader, virtual_fs_repo):
    class MockArtifactoryAccessor(_ArtifactoryAccessor):
        def __init__(self) -> None:
            super().__init__()
            self._galactory_fixture_loader = fixture_loader

        def get_stat_json(self, pathobj, key=None):
            loader = self._galactory_fixture_loader
            repo = pathobj._galactory_mocked_path

            if pathobj.is_dir():
                data = loader.load_json('artifactory/responses/stat_dir')
                # children = repo.listdir(repo)
                data['children'] = [dict(uri='/' + child.name) for child in repo.iterdir()]
                data['uri'] = str(pathobj)
                data['repo'] = virtual_fs_repo.name
                data['path'] = data['uri'].split(f"/{data['repo']}/", 1)[1]
            else:
                data = loader.load_json('artifactory/responses/stat_file')
                data['downloadUri'] = data['uri'] = str(pathobj)
                data['repo'] = virtual_fs_repo.name
                data['path'] = data['uri'].split(f"/{data['repo']}/", 1)[1]

            return data

    return MockArtifactoryAccessor


@pytest.fixture
def mock_artifactory_path(mock_artifactory_accessor, virtual_fs_repo):
    _artifactory_accessor = mock_artifactory_accessor()

    class MockArtifactoryPath(ArtifactoryPath):
        def _new__new__(cls, *args, **kwargs):
            obj = super().__new__(cls, *args, **kwargs)
            rel = str(obj).split('/repo/', 1)[1]
            obj._galactory_mocked_path = virtual_fs_repo / rel
            obj._n = True
            return obj

        def _new_make_child(self, args):
            obj = super()._make_child(args)
            return self._galactory_copy_attrs(obj)

        def _new_make_child_relpath(self, args):
            obj = super()._make_child_relpath(args)
            return self._galactory_copy_attrs(obj)

        if sys.version_info.major == 3 and sys.version_info.minor >= 10:
            _accessor = _artifactory_accessor
            __new__ = _new__new__
            _make_child = _new_make_child
            _make_child_relpath = _new_make_child_relpath
        else:
            # in 3.9 and below Pathlib limits what members can be present in 'Path' class
            __slots__ = ("auth", "verify", "cert", "session", "timeout", "_galactory_mocked_path")

        def _init(self, *args, **kwargs):
            new = super()._init(*args, template=_FakePathTemplate(_artifactory_accessor), **kwargs)
            rel = str(self).split('/repo/', 1)[1]
            self._galactory_mocked_path = virtual_fs_repo / rel
            return new

        def is_dir(self):
            repo = self._galactory_mocked_path
            if repo.is_dir() and not repo.name.endswith('.tar.gz'):
                return True
            else:
                return False
            # return super().is_dir()

        def _galactory_copy_attrs(self, obj):
            obj._galactory_mocked_path = self._galactory_mocked_path
            return obj

        @property
        def _galactory_manifest_path(self):
            return self._galactory_mocked_path / 'MANIFEST.json'

        def _galactory_get_manifest(self, key=None):
            with self._galactory_manifest_path.open() as f:
                manifest = json.load(f)

            if key:
                return manifest.get(key)
            return manifest

        @property
        def properties(self):
            if self.is_dir():
                return {}

            ci = self._galactory_get_manifest('collection_info')

            return {
                'collection_info': [json.dumps(ci)],
                'fqcn': [f"{ci['namespace']}.{ci['name']}"],
                'namespace': [ci['namespace']],
                'name': [ci['name']],
                'version': [ci['version']],
            }

    return MockArtifactoryPath


@pytest.fixture
def repository(mock_artifactory_path):
    return mock_artifactory_path('http://artifactory.example.com/repo/subpath')
