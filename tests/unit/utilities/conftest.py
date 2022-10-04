# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

import pytest
from unittest import mock

from galactory.utilities import discover_collections as original_discover_collections


@pytest.fixture
def manifest_loader():
    def _load(repo):
        return repo._galactory_get_manifest()

    loader = mock.Mock(wraps=_load)

    with mock.patch('galactory.utilities.load_manifest_from_archive', loader):
        yield loader


@pytest.fixture
def discover_collections(manifest_loader):
    _discover = mock.Mock(wraps=original_discover_collections)
    with mock.patch('galactory.utilities.discover_collections', _discover):
        yield _discover
