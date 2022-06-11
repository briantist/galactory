# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

import pytest
import os
import json

from unittest import mock
# pytest_plugins = ["docker_compose"]


@pytest.fixture(scope='session')
def disable_http():
    def _unexpected_request(self, method, url, *args, **kwargs):
        raise RuntimeError(f"Attempt to make {method} request to {self.scheme}://{self.host}{url}")

    with mock.patch('urllib3.connectionPool.urlopen', _unexpected_request):
        yield


@pytest.fixture(scope='session')
def fixture_finder():
    def _finder(*paths):
        here = os.path.dirname(os.path.realpath(__file__))
        fixture = os.path.join(here, 'fixtures', *paths)
        return fixture
    return _finder


@pytest.fixture(scope='session')
def fixture_loader(fixture_finder):
    class FixtureLoader:
        @staticmethod
        def _finder(relative_path, implied_extension=None):
            fixture = fixture_finder(relative_path)
            if implied_extension and not os.path.splitext(fixture)[1]:
                fixture = '.'.join([fixture, implied_extension])

            return fixture

        @classmethod
        def load_json(cls, relative_path):
            with open(cls._finder(relative_path, implied_extension='json'), 'r') as f:
                return json.load(f)

    return FixtureLoader
