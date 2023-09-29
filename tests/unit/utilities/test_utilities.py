# -*- coding: utf-8 -*-
# (c) 2023 Brian Scholer (@briantist)

import pytest
from unittest import mock

from datetime import datetime, timedelta
from types import GeneratorType
import semver

from galactory.utilities import _latest_collection_version


@pytest.mark.parametrize(["ref", "dif", "exp"], [
    ("0.0.0-dev0", "0.0.0-dev1", "0.0.0-dev1"),
    ("0.0.0", "0.0.0-dev1", "0.0.0"),
    ("1.2.3", "1.2.4", "1.2.4"),
    ("0.0.0-dev0", "0.0.0-dev1", "0.0.0-dev1"),
    ("0.0.0", "99.99.99-dev1", "0.0.0"),
])
@pytest.mark.parametrize("prop", [None, "semver", "other"])
def test_latest_collection_version(ref, dif, exp, prop):
    reference = semver.VersionInfo.parse(ref)
    difference = semver.VersionInfo.parse(dif)
    expected = ref if exp == ref else dif

    opprop = {}
    if prop is None:
        expprop = "semver"
    else:
        opprop["property"] = expprop = prop

    # ensure we didn't mess up the test cases
    assert expected in [reference, difference]

    result = _latest_collection_version({expprop: reference}, {expprop: difference}, **opprop)

    assert result[expprop] == expected
