# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

import semver
from base64io import Base64IO
from flask import Response, jsonify, abort, url_for, request, current_app

from . import bp as v2
from ... import constants as C
from ...utilities import (
    discover_collections,
    collected_collections,
    _collection_listing,
    authorize,
    _chunk_to_temp,
    upload_collection_from_hashed_tempfile,
)
from ...upstream import ProxyUpstream
from ...models import CollectionCollection


@v2.route('/collections')
@v2.route('/collections/', endpoint='collections')
def collections():
    repository = authorize(request, current_app.config['ARTIFACTORY_PATH'])
    scheme = current_app.config.get('PREFERRED_URL_SCHEME')

    results = []
    colcol = CollectionCollection.from_collections(discover_collections(repo=repository, scheme=scheme))

    for colgroup in colcol.values():
        result = {
            'href': url_for(
                f"{request.blueprint}.collection",
                namespace=colgroup.namespace,
                collection=colgroup.name,
                _external=True,
                _scheme=scheme
            ),
            'name': colgroup.name,
            'namespace': {
                'name': colgroup.namespace,
            },
            'deprecated': False, # FIXME
            'created': colgroup.latest.created,
            'modified': colgroup.latest.modified,
            'versions_url': url_for(
                f"{request.blueprint}.versions",
                namespace=colgroup.latest.namespace,
                collection=colgroup.latest.name,
                _external=True,
                _scheme=scheme,
            ),
            'latest_version': {
                'href': url_for(
                    f"{request.blueprint}.version",
                    namespace=colgroup.latest.namespace,
                    collection=colgroup.latest.name,
                    version=colgroup.latest.version,
                    _external=True,
                    _scheme=scheme,
                ),
                "version": colgroup.latest.version,
            },
        }
        results.append(result)

    return jsonify(count=len(results), results=results, next=None, next_link=None, previous=None, previous_link=None)


@v2.route('/collections/<namespace>/<collection>')
@v2.route('/collections/<namespace>/<collection>/', endpoint='collection')
def collection(namespace, collection):
    repository = authorize(request, current_app.config['ARTIFACTORY_PATH'])
    upstream = current_app.config['PROXY_UPSTREAM']
    no_proxy = current_app.config['NO_PROXY_NAMESPACES']
    cache_minutes = current_app.config['CACHE_MINUTES']
    cache_read = current_app.config['CACHE_READ']
    cache_write = current_app.config['CACHE_WRITE']
    scheme = current_app.config.get('PREFERRED_URL_SCHEME')

    upstream_result = None
    if upstream and (not no_proxy or namespace not in no_proxy):
        proxy = ProxyUpstream(repository, upstream, cache_read, cache_write, cache_minutes)
        upstream_result = proxy.proxy(request)

    colcol = CollectionCollection.from_collections(discover_collections(repo=repository, namespace=namespace, name=collection, scheme=scheme))


    if not (colcol or upstream_result):
        abort(C.HTTP_NOT_FOUND)

    colgroup = None
    if colcol:
        if len(colcol) > 1:
            abort(C.HTTP_INTERNAL_SERVER_ERROR)
        colgroup = next(iter(colcol.values()))

    if upstream_result:
        if colgroup is None:
            result = upstream_result
        else:
            try:
                upstream_version = VersionInfo.parse(upstream_result['latest_version']['version'])
            except (KeyError, ValueError):
                # TODO: warn?
                pass
            else:
                if colgroup.latest < upstream_version:
                    return upstream_result

    result = {
        'href': url_for(
            f"{request.blueprint}.collection",
            namespace=colgroup.namespace,
            collection=colgroup.name,
            _external=True,
            _scheme=scheme
        ),
        'name': colgroup.latest.name,
        'namespace': {
            'name': colgroup.latest.namespace,
        },
        'deprecated': False, # FIXME
        'created': colgroup.latest.created,
        'modified': colgroup.latest.modified,
        'versions_url': url_for(
            f"{request.blueprint}.versions",
            namespace=colgroup.latest.namespace,
            collection=colgroup.latest.name,
            _external=True,
            _scheme=scheme,
        ),
        'latest_version': {
            'href': url_for(
                f"{request.blueprint}.version",
                namespace=colgroup.latest.namespace,
                collection=colgroup.latest.name,
                version=colgroup.latest.version,
                _external=True,
                _scheme=scheme,
            ),
            "version": colgroup.latest.version,
        },
    }
    return result


@v2.route('/collections/<namespace>/<collection>/versions')
@v2.route('/collections/<namespace>/<collection>/versions/')
def versions(namespace, collection):
    results = []
    repository = authorize(request, current_app.config['ARTIFACTORY_PATH'])
    upstream = current_app.config['PROXY_UPSTREAM']
    no_proxy = current_app.config['NO_PROXY_NAMESPACES']
    cache_minutes = current_app.config['CACHE_MINUTES']
    cache_read = current_app.config['CACHE_READ']
    cache_write = current_app.config['CACHE_WRITE']
    scheme = current_app.config.get('PREFERRED_URL_SCHEME')

    upstream_result = None
    if upstream and (not no_proxy or namespace not in no_proxy):
        proxy = ProxyUpstream(repository, upstream, cache_read, cache_write, cache_minutes)
        upstream_result = proxy.proxy(request)

    collections = collected_collections(repository, namespace=namespace, name=collection, scheme=scheme)

    if not (collections or upstream_result):
        abort(C.HTTP_NOT_FOUND)

    if len(collections) > 1:
        abort(C.HTTP_INTERNAL_SERVER_ERROR)

    vers = set()
    for _, c in collections.items():
        for v, i in c['versions'].items():
            results.append(
                {
                    'href': url_for(
                        'api.v2.version',
                        namespace=i['namespace']['name'],
                        collection=i['name'],
                        version=v,
                        _external=True,
                        _scheme=scheme,
                    ),
                    'version': v,
                }
            )
            vers.add(v)

    if upstream_result:
        for item in upstream_result['results']:
            if item['version'] not in vers:
                results.append(item)

    out = {
        'count': len(results),
        'next': None,
        'previous': None,
        'results': results,
    }
    return jsonify(out)


@v2.route('/collections/<namespace>/<collection>/versions/<version>')
@v2.route('/collections/<namespace>/<collection>/versions/<version>/')
def version(namespace, collection, version):
    repository = authorize(request, current_app.config['ARTIFACTORY_PATH'])
    upstream = current_app.config['PROXY_UPSTREAM']
    no_proxy = current_app.config['NO_PROXY_NAMESPACES']
    cache_minutes = current_app.config['CACHE_MINUTES']
    cache_read = current_app.config['CACHE_READ']
    cache_write = current_app.config['CACHE_WRITE']
    scheme = current_app.config.get('PREFERRED_URL_SCHEME')

    try:
        info = next(discover_collections(repository, namespace=namespace, name=collection, version=version, scheme=scheme))
    except StopIteration:
        if upstream and (not no_proxy or namespace not in no_proxy):
            proxy = ProxyUpstream(repository, upstream, cache_read, cache_write, cache_minutes)
            upstream_result = proxy.proxy(request)
            return jsonify(upstream_result)
        else:
            abort(C.HTTP_NOT_FOUND)

    out = {
        'artifact': {
            'filename': info['filename'],
            'sha256': info['sha256'],
            'size': info['size'],
        },
        'collection': {
            'href': url_for(
                'api.v2.collection',
                namespace=namespace,
                collection=collection,
                _external=True,
                _scheme=scheme,
            ),
            'name': info['name'],
        },
        'namespace': info['namespace'],
        'download_url': info['download_url'],
        'hidden': False,
        'href': url_for(request.endpoint, _external=True, _scheme=scheme, **request.view_args),
        'id': 0,
        'metadata': info['collection_info'],
        'version': version,
    }
    return jsonify(out)


@v2.route('/collections', methods=['POST'])
@v2.route('/collections/', methods=['POST'])
def publish():
    sha256 = request.form['sha256']
    file = request.files['file']
    skip_configured_auth = current_app.config['PUBLISH_SKIP_CONFIGURED_AUTH']
    property_fallback = current_app.config.get('USE_PROPERTY_FALLBACK', False)
    _scheme = current_app.config.get('PREFERRED_URL_SCHEME')

    target = authorize(request, current_app.config['ARTIFACTORY_PATH'] / file.filename, skip_configured_auth=skip_configured_auth)

    with _chunk_to_temp(Base64IO(file)) as tmp:
        if tmp.sha256 != sha256:
            abort(Response(f"Hash mismatch: uploaded=='{sha256}', calculated=='{tmp.sha256}'", C.HTTP_INTERNAL_SERVER_ERROR))

        upload_collection_from_hashed_tempfile(target, tmp, property_fallback=property_fallback)

    return jsonify(task=url_for('api.v2.import_singleton', _external=True, _scheme=_scheme))
