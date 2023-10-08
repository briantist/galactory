# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

import json
import math
import hashlib
import gzip

import typing as t

from datetime import datetime
from tempfile import SpooledTemporaryFile
from urllib3 import Retry
from requests.adapters import HTTPAdapter
from requests import Session
from base64io import Base64IO

from flask import current_app, abort, Response, Request
from flask.json.provider import DefaultJSONProvider
from artifactory import ArtifactoryPath, ArtifactoryException
from dohq_artifactory.auth import XJFrogArtApiAuth, XJFrogArtBearerAuth

from . import constants as C
from .models import CollectionData
from .iter_tar import iter_tar


class DateTimeIsoFormatJSONProvider(DefaultJSONProvider):
    @staticmethod
    def default(o: t.Any) -> t.Any:
        if isinstance(o, datetime):
            return o.isoformat()

        return super().default(o)


def _session_with_retries(retry=None, auth=None) -> Session:
    if retry is None:
        retry = Retry(connect=5, read=3, redirect=2, status=6, other=3, backoff_factor=0.1, raise_on_status=False)

    adapter = HTTPAdapter(max_retries=retry)
    session = Session()
    session.auth = auth
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    return session


def authorize(request: Request, artifactory_path: ArtifactoryPath, retry=None, skip_configured_auth: bool = False) -> ArtifactoryPath:
    auth = None
    if not skip_configured_auth:
        accesstoken = current_app.config['ARTIFACTORY_ACCESS_TOKEN']
        apikey = current_app.config['ARTIFACTORY_API_KEY']
        if accesstoken is not None:
            auth = XJFrogArtBearerAuth(accesstoken)
        elif apikey is not None:
            auth = XJFrogArtApiAuth(apikey)

    if current_app.config['USE_GALAXY_AUTH'] and (not current_app.config['PREFER_CONFIGURED_AUTH'] or auth is None):
        galaxy_auth_type = current_app.config['GALAXY_AUTH_TYPE']
        authorization = request.headers.get('Authorization')
        if authorization:
            token = authorization.split(' ')[1]
            if galaxy_auth_type == 'access_token':
                auth = XJFrogArtBearerAuth(token)
            elif galaxy_auth_type == 'api_key':
                auth = XJFrogArtApiAuth(token)
            else:
                raise ValueError(f"Unknown galaxy auth type '{galaxy_auth_type}'.")

    session = _session_with_retries(retry=retry, auth=auth)
    return ArtifactoryPath(artifactory_path, session=session)


def load_manifest_from_archive(handle, seek_to_zero_after=True):
    with gzip.GzipFile(fileobj=handle, mode='rb') as gz:
        for fname, data in iter_tar(gz):
            if fname.lower() in ('manifest.json', './manifest.json'):
                data = json.loads(data)
                if seek_to_zero_after:
                    handle.seek(0)
                return data


def discover_collections(
    repo: ArtifactoryPath,
    namespace: str = None,
    name: str = None,
    version: str = None,
    fast_detection: bool = True,
):
    for p in repo:
        if fast_detection:
            # we're going to use the naming convention to eliminate candidates early,
            # to avoid excessive additional requests for properties and stat that slow
            # down the listing immensely as the number of collections grows.
            try:
                f_namespace, f_name, f_version = p.name.replace('.tar.gz', '').split('-', maxsplit=2)
            except ValueError:
                pass
            else:
                if not all(
                    (
                        not namespace or f_namespace == namespace,
                        not name or f_name == name,
                        not version or f_version == version
                    )
                ):
                    continue

        info = p.stat()
        if info.is_dir:
            continue

        props = p.properties
        if not props.get('collection_info'):
            continue

        coldata = CollectionData.from_artifactory_path(path=p, properties=props, stat=info)

        if all(
            (
                not namespace or coldata.namespace == namespace,
                not name or coldata.name == name,
                not version or coldata.version == version
            )
        ):
            yield coldata


def lcm(a, b, *more):
    z = lcm(b, *more) if more else b
    return abs(a * z) // math.gcd(a, z)


class IncomingCollectionStream:
    def __new__(cls, stream: t.IO, *, format: str = None):
        if format == 'raw':
            return stream
        if format == 'base64':
            return Base64IO(stream)
        return cls.detected_stream(stream)

    @staticmethod
    def detected_stream(stream: t.IO):
        with gzip.GzipFile(fileobj=stream, mode='rb') as gz:
            try:
                gz.read(1)
            except gzip.BadGzipFile:
                return Base64IO(stream)
            else:
                return stream
            finally:
                stream.seek(0)


class HashedTempFile():
    def __init__(self, handle, md5, sha1, sha256, close=True) -> None:
        self.handle = handle
        self.md5 = md5
        self.sha1 = sha1
        self.sha256 = sha256
        self._close = close

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if self._close:
            self.handle.close()


def _chunk_to_temp(fsrc, iterator=None, spool_size=5*1024*1024, seek_to_zero=True, chunk_multiplier=64, close=True) -> HashedTempFile:
    md5sum = hashlib.md5()
    sha1sum = hashlib.sha1()
    sha256sum = hashlib.sha256()
    common_block_size = lcm(md5sum.block_size, sha1sum.block_size, sha256sum.block_size)
    chunk_size = chunk_multiplier * common_block_size

    it = iter(lambda: fsrc.read(chunk_size), b'') if iterator is None else iterator(chunk_size)

    tmp = SpooledTemporaryFile(max_size=spool_size)

    for chunk in it:
        md5sum.update(chunk)
        sha1sum.update(chunk)
        sha256sum.update(chunk)
        tmp.write(chunk)

    if seek_to_zero:
        tmp.seek(0)

    return HashedTempFile(tmp, md5sum.hexdigest(), sha1sum.hexdigest(), sha256sum.hexdigest(), close=close)


def upload_collection_from_hashed_tempfile(artifact: ArtifactoryPath, tmpfile: HashedTempFile, property_fallback: bool = False) -> t.Dict[str, t.Any]:
    try:
        manifest = load_manifest_from_archive(tmpfile.handle)
    except Exception:
        abort(Response("Error loading manifest from collection archive.", C.HTTP_INTERNAL_SERVER_ERROR))
    else:
        ci = manifest['collection_info']
        props = {
            'collection_info': json.dumps(ci),
            'namespace': ci['namespace'],
            'name': ci['name'],
            'version': ci['version'],
            'fqcn': f"{ci['namespace']}.{ci['name']}"
        }

    params = props
    if property_fallback:
        params = {}

    try:
        artifact.deploy(
            tmpfile.handle,
            md5=tmpfile.md5,
            sha1=tmpfile.sha1,
            sha256=tmpfile.sha256,
            parameters=params,
            quote_parameters=True
        )
    except ArtifactoryException as exc:
        cause = exc.__cause__
        current_app.logger.debug(cause)
        abort(Response(cause.response.text, cause.response.status_code))
    else:
        if property_fallback:
            artifact.properties = props

    return props
