# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

import pytest

from datetime import datetime, timezone

from galactory.models import CollectionData


@pytest.fixture
def collection_data(request) -> CollectionData:
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
    overrides = getattr(request, 'param', {})
    values.update(overrides)
    return CollectionData(**values)
