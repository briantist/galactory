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


@v2.route('/collections')
@v2.route('/collections/')
def collections():
    results = _collection_listing(current_app.config['ARTIFACTORY_PATH'])
    return jsonify(results=results)


@v2.route('/collections/<namespace>/<collection>')
@v2.route('/collections/<namespace>/<collection>/')
def collection(namespace, collection):
    repository = authorize(request, current_app.config['ARTIFACTORY_PATH'])
    upstream = current_app.config['PROXY_UPSTREAM']
    no_proxy = current_app.config['NO_PROXY_NAMESPACES']
    cache_minutes = current_app.config['CACHE_MINUTES']
    cache_read = current_app.config['CACHE_READ']
    cache_write = current_app.config['CACHE_WRITE']

    upstream_result = None
    if upstream and (not no_proxy or namespace not in no_proxy):
        proxy = ProxyUpstream(repository, upstream, cache_read, cache_write, cache_minutes)
        upstream_result = proxy.proxy(request)

    results = _collection_listing(repository, namespace, collection)

    if not (results or upstream_result):
        abort(C.HTTP_NOT_FOUND)

    result = None
    if results:
        if len(results) > 1:
            abort(C.HTTP_INTERNAL_SERVER_ERROR)
        result = results[0]

    if upstream_result:
        if result is None:
            result = upstream_result
        else:
            result = max((result, upstream_result), key=lambda r: semver.VersionInfo.parse(r['latest_version']['version']))

    return jsonify(result)


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

    upstream_result = None
    if upstream and (not no_proxy or namespace not in no_proxy):
        proxy = ProxyUpstream(repository, upstream, cache_read, cache_write, cache_minutes)
        upstream_result = proxy.proxy(request)

    collections = collected_collections(repository, namespace=namespace, name=collection)

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

    try:
        info = next(discover_collections(repository, namespace=namespace, name=collection, version=version))
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
            'href': url_for('api.v2.collection', namespace=namespace, collection=collection, _external=True),
            'name': info['name'],
        },
        'namespace': info['namespace'],
        'download_url': info['download_url'],
        'hidden': False,
        'href': request.url,
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
    skip_configured_key = current_app.config['PUBLISH_SKIP_CONFIGURED_KEY']

    target = authorize(request, current_app.config['ARTIFACTORY_PATH'] / file.filename, skip_configured_key=skip_configured_key)

    with _chunk_to_temp(Base64IO(file)) as tmp:
        if tmp.sha256 != sha256:
            abort(Response(f"Hash mismatch: uploaded=='{sha256}', calculated=='{tmp.sha256}'", C.HTTP_INTERNAL_SERVER_ERROR))

        upload_collection_from_hashed_tempfile(target, tmp)

    return jsonify(task=url_for('api.v2.import_singleton', _external=True))
