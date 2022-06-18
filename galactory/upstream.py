# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

import requests
import json

from contextlib import contextmanager
from io import StringIO
from datetime import datetime, timedelta
from artifactory import ArtifactoryException

from flask import current_app, abort, Response

from . import constants as C


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

    def __init__(self, data=None, metadata=None, expiry_delta=timedelta(hours=1), calculate_expiry_on_read=False) -> None:
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

    def __init__(self, repository, upstream_url) -> None:
        self._repository = repository
        self._upstream = upstream_url

    def _get_cache(self, request, **kwargs) -> _CacheEntry:
        path = self._repository / self._cache_path / request.path / 'data.json'

        try:
            with path.open() as f:
                return _CacheEntry.from_file(f, **kwargs)
        except ArtifactoryException:
            return _CacheEntry(**kwargs)

    def _set_cache(self, request, cache) -> None:
        from . import DateTimeIsoFormatJSONEncoder

        path = self._repository / self._cache_path / request.path / 'data.json'
        buffer = StringIO()
        cache.update()
        json.dump(cache._to_serializable_dict(), buffer, cls=DateTimeIsoFormatJSONEncoder)
        buffer.seek(0)
        path.deploy(buffer)
        buffer.close()

    def proxy(self, request):
        cache = self._get_cache(request)

        if cache.empty or cache.expired:
            req = self._rewrite_to_upstream(request, self._upstream)
            with requests.Session() as s:
                try:
                    resp = s.send(req)
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
                    current_app.logger.info(f"Cache miss: {request.url}")
                    data = self._rewrite_upstream_response(resp.json(), request.url_root)
                    cache.data = data
                    self._set_cache(request, cache)
        else:
            current_app.logger.info(f"Cache hit: {request.url}")

        return cache.data

    def _rewrite_upstream_response(self, response_data, url_root) -> dict:
        ret = {}
        for k, v in response_data.items():
            if isinstance(v, dict):
                ret[k] = self._rewrite_upstream_response(v, url_root)
            elif isinstance(v, list):
                ret[k] = [self._rewrite_upstream_response(d, url_root) if isinstance(d, dict) else d for d in v]
            elif isinstance(v, str) and v.startswith(self._upstream):
                if 'api/v1' in v:
                    continue
                ret[k] = v.replace(self._upstream, url_root)
            elif k == 'id':
                continue
            else:
                ret[k] = v

        return ret

    def _rewrite_to_upstream(self, request, upstream_url, prepared=True):
        this_url = request.url
        this_root = request.url_root
        rewritten = this_url.replace(this_root, upstream_url)

        current_app.logger.info(f"Rewriting '{this_url}' to '{rewritten}'")

        headers = {k: v for k, v in request.headers.items() if k not in ['Authorization', 'Host']}

        req = requests.Request(method=request.method, url=rewritten, headers=headers, data=request.data)

        if prepared:
            prepared = req.prepare()
            current_app.logger.info(prepared.url)
            current_app.logger.info(prepared.body)
            current_app.logger.info(prepared.headers)
            return prepared

        return req
