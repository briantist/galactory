# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

import requests
import json

from contextlib import contextmanager
from io import StringIO
from datetime import datetime, timedelta
from artifactory import ArtifactoryException

from flask import current_app, abort, Response, url_for

from . import constants as C
from .utilities import _session_with_retries, DateTimeIsoFormatJSONProvider

class _CacheEntry:
    _raw = {}

    @classmethod
    def from_file(cls, f, **kwargs):
        def _time_decoder(pairs):
            d = {}
            for k, v in pairs:
                try:
                    nv = datetime.fromisoformat(v)
                except (ValueError, TypeError):
                    d[k] = v
                else:
                    d[k] = nv

            return d

        loaded = json.load(f, object_pairs_hook=_time_decoder)
        return cls(data=loaded['data'], metadata=loaded['metadata'], **kwargs)

    def __init__(self, expiry_delta, data=None, metadata=None, calculate_expiry_on_read=True) -> None:
        raw = {'metadata': {}, 'data': {}}
        self._expiry_delta = expiry_delta
        self._calc_on_read = calculate_expiry_on_read
        if data is not None:
            raw['data'] = data.copy()

        if metadata is not None:
            raw['metadata'] = metadata.copy()

        self._raw = raw

    @property
    def empty(self) -> bool:
        return not (self._raw.get('data') and self._raw.get('metadata'))

    @property
    def created(self) -> datetime:
        if self.empty:
            return None

        return self.metadata.get('created')

    @property
    def expires(self) -> datetime:
        if self.empty:
            return None

        if self._calc_on_read:
            if self.created is None:
                return None

            return self.created + self._expiry_delta
        else:
            return self.metadata.get('expires')

    @property
    def expired(self) -> bool:
        expires = self.expires
        return expires is not None and datetime.utcnow() >= expires

    @property
    def metadata(self) -> dict:
        return self._raw['metadata']

    @property
    def data(self) -> dict:
        return self._raw['data']

    @data.setter
    def data(self, value) -> None:
        self._raw['data'] = value
        self.metadata['dirty'] = True

    @property
    def dirty(self) -> bool:
        return self.metadata.get('dirty', False)

    def update(self, force=False):
        if not (force or self.dirty):
            return

        now = datetime.utcnow()
        self.metadata['created'] = now
        self.metadata['expires'] = now + self._expiry_delta
        self.metadata['dirty'] = False

    def _to_serializable_dict(self):
        o = {
            'data': self.data,
            'metadata': self.metadata.copy(),
        }
        o['metadata'].pop('dirty')
        return o


class ProxyUpstream:
    _cache_path = '_cache'

    def __init__(self, repository, upstream_url, read_cache, write_cache, cache_expiry_minutes) -> None:
        self._repository = repository
        self._upstream = upstream_url
        self._read_cache = read_cache
        self._write_cache = write_cache
        self._cache_expiry_delta = timedelta(minutes=cache_expiry_minutes)


    def _get_cache(self, request, expiry_delta=None, **kwargs) -> _CacheEntry:
        path = self._repository / self._cache_path / request.path / 'data.json'

        if expiry_delta is None:
            expiry_delta = self._cache_expiry_delta

        if not self._read_cache:
            return _CacheEntry(expiry_delta=expiry_delta, **kwargs)

        try:
            with path.open() as f:
                return _CacheEntry.from_file(f, expiry_delta=expiry_delta, **kwargs)
        except ArtifactoryException:
            return _CacheEntry(expiry_delta=expiry_delta, **kwargs)

    def _set_cache(self, request, cache) -> None:
        if not self._write_cache:
            return

        path = self._repository / self._cache_path / request.path / 'data.json'
        with StringIO() as buffer:
            cache.update()
            json.dump(cache._to_serializable_dict(), buffer, default=DateTimeIsoFormatJSONProvider.default)
            buffer.seek(0)
            path.deploy(buffer, quote_parameters=True)

    @contextmanager
    def proxy_download(self, request):
        no_rewrite = C.QUERY_DOWNLOAD_UPSTREAM_URL in request.args
        if no_rewrite:
            upstream_url = request.args[C.QUERY_DOWNLOAD_UPSTREAM_URL]
        else:
            upstream_url = self._upstream

        req = self._rewrite_to_upstream(request, upstream_url, no_rewrite=no_rewrite, no_paginate=True)
        with _session_with_retries() as s:
            try:
                # Merge environment settings into session
                settings = s.merge_environment_settings(req.url, proxies={}, stream=True, verify=None, cert=None)
                resp = s.send(req, **settings)
                resp.raise_for_status()
            except:
                abort(Response(resp.text, resp.status_code))
            else:
                try:
                    yield resp
                finally:
                    resp.close()

    def proxy(self, request):
        cache = self._get_cache(request)
        scheme = current_app.config.get('PREFERRED_URL_SCHEME')

        if cache.empty or cache.expired:
            req = self._rewrite_to_upstream(request, self._upstream)
            with _session_with_retries() as s:
                try:
                    # Merge environment settings into session
                    settings = s.merge_environment_settings(req.url, proxies={}, stream=None, verify=None, cert=None)
                    resp = s.send(req, **settings)
                    resp.raise_for_status()
                except requests.exceptions.HTTPError:
                    infoer = current_app.logger.debug if resp.status_code == C.HTTP_NOT_FOUND else current_app.logger.warning
                    infoer("Upstream results not available, got HTTP %i: %s", resp.status_code, resp.text)
                    if cache.expired:
                        current_app.logger.info(f"Cache hit (expired, upstream error): {request.url}")
                        return cache.data
                    # else:
                        # abort(Response(resp.text, resp.status_code))

                else:
                    if self._read_cache:
                        current_app.logger.info(f"Cache miss: {request.url}")

                    data = resp.json()
                    cache.data = data

                    if self._write_cache:
                        self._set_cache(request, cache)
        else:
            current_app.logger.info(f"Cache hit: {request.url}")

        return self._rewrite_upstream_response(cache.data, url_for('root.index', _external=True, _scheme=scheme))

    def _rewrite_upstream_response(self, response_data, url_root) -> dict:
        # Remove these keys from the response.
        # If the value is not None, only remove when the type matches.
        _REMOVE_FIELDS = {
            # TODO: should id refer to some Artifactory ID?
            'id': (int, str),
            # TODO: use artifactory download count, or combine with upstream?
            'download_count': int,
        }

        # Leave these fields in the response without alteration or
        # further processing. Same rules as _REMOVE_FIELDS.
        _SKIP_FIELDS = {
            # This field is an absolute URL, and will not necessarily map to
            # a known API path, even if it does in public Galaxy.
            # We will leave it unadultered and let the API paths that expect
            # this field to overwrite it or not.
            'download_url': None,
        }

        ret = {}
        for k, v in response_data.items():
            if k in _SKIP_FIELDS and (_SKIP_FIELDS[k] is None or isinstance(v, _SKIP_FIELDS[k])):
                ret[k] = v
                continue
            if k in _REMOVE_FIELDS and (_REMOVE_FIELDS[k] is None or isinstance(v, _REMOVE_FIELDS[k])):
                continue

            if isinstance(v, dict):
                ret[k] = self._rewrite_upstream_response(v, url_root)
            elif isinstance(v, list):
                ret[k] = [self._rewrite_upstream_response(d, url_root) if isinstance(d, dict) else d for d in v]
            elif isinstance(v, str) and v.startswith(self._upstream):
                if 'api/v1' in v:
                    continue
                ret[k] = v.replace(self._upstream, url_root)
            else:
                ret[k] = v

        return ret

    def _rewrite_to_upstream(self, request, upstream_url, *, prepared=True, no_rewrite=False, no_paginate=False):
        this_url = request.base_url
        this_root = request.url_root
        if no_rewrite:
            params = {}
            rewritten = upstream_url
            current_app.logger.info(f"Not rewriting '{this_url}'; using '{rewritten}'")
        else:
            rewritten = this_url.replace(this_root, upstream_url)
            current_app.logger.info(f"Rewriting '{this_url}' to '{rewritten}'")
            params = request.args.copy()
            if not no_paginate:
                if 'v2' in this_url:
                    params['page_size'] = 100
                else:
                    params['limit'] = 100

        headers = {k: v for k, v in request.headers.items() if k not in ['Authorization', 'Host']}
        headers['Accept'] = 'application/json, */*'

        req = requests.Request(method=request.method, url=rewritten, headers=headers, data=request.data, params=params)

        if prepared:
            prepared = req.prepare()
            current_app.logger.info(prepared.url)
            current_app.logger.info(prepared.body)
            current_app.logger.info(prepared.headers)
            return prepared

        return req
