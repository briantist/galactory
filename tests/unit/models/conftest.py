# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

import pytest
import typing as t

from datetime import datetime, timezone
from functools import partial

from galactory.models import CollectionData


@pytest.fixture
def collection_data_factory() -> t.Callable[[], CollectionData]:
    values = dict(
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
    return partial(CollectionData, **values)


@pytest.fixture
def collection_data(request, collection_data_factory) -> CollectionData:
    overrides = getattr(request, 'param', {})
    return collection_data_factory(**overrides)
