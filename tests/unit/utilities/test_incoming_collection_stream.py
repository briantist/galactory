# -*- coding: utf-8 -*-
# (c) 2023 Brian Scholer (@briantist)

import pytest
import tarfile

from pathlib import Path
from base64io import Base64IO
from galactory.utilities import IncomingCollectionStream


@pytest.fixture
def collection_tarball(virtual_fs_repo: Path, tmp_path: Path):
    collection = next(virtual_fs_repo.glob("**/*.tar.gz"))
    gz_path = tmp_path / collection.name
    with tarfile.open(gz_path, mode='w:gz') as tar:
        tar.add(collection)
    return gz_path


@pytest.fixture
def base64_tarball(collection_tarball: Path, tmp_path: Path):
    b64_path = tmp_path / f"{collection_tarball.name}.b64"
    with open(collection_tarball, mode='rb') as raw, open(b64_path, mode='wb') as w, Base64IO(w) as f:
        f.write(raw.read())
    return b64_path


class TestIncomingCollectionStream:
    @pytest.mark.parametrize('format', [None, 'auto', 'undefined', 'raw'])
    def test_raw(self, collection_tarball: Path, format: str):
        with open(collection_tarball, mode='rb') as f:
            assert IncomingCollectionStream.detected_stream(f) is f
            assert IncomingCollectionStream(f, format=format)

    @pytest.mark.parametrize('format', [None, 'auto', 'undefined', 'base64'])
    def test_base64(self, base64_tarball: Path, format: str):
        with open(base64_tarball, mode='rb') as f:
            assert isinstance(IncomingCollectionStream.detected_stream(f), Base64IO)
            assert isinstance(IncomingCollectionStream(f, format=format), Base64IO)
