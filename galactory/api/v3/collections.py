# -*- coding: utf-8 -*-
# (c) 2023 Brian Scholer (@briantist)

from semver import VersionInfo
from flask import Response, jsonify, abort, url_for, request, current_app

from . import bp as v3
from ... import constants as C
from ...utilities import (
    discover_collections,
    authorize,
    _chunk_to_temp,
    upload_collection_from_hashed_tempfile,
    IncomingCollectionStream,
)
from ...upstream import ProxyUpstream
from ...models import CollectionCollection


@v3.route('/collections')
@v3.route('/collections/')
@v3.route('/plugin/ansible/content/published/collections/index')
@v3.route('/plugin/ansible/content/published/collections/index/', endpoint='collections')
def collections():
    repository = authorize(request, current_app.config['ARTIFACTORY_PATH'])
    scheme = current_app.config.get('PREFERRED_URL_SCHEME')

    results = []
    colcol = CollectionCollection.from_collections(discover_collections(repo=repository))

    for colgroup in colcol.values():
        result = {
            'href': url_for(
                ".collection",
                namespace=colgroup.namespace,
                collection=colgroup.name,
                _external=False,
                _scheme=scheme
            ),
            'name': colgroup.name,
            'namespace': colgroup.namespace,
            'deprecated': False, # FIXME
            'created_at': colgroup.latest.created,
            'updated_at': colgroup.latest.modified,
            'versions_url': url_for(
                ".versions",
                namespace=colgroup.latest.namespace,
                collection=colgroup.latest.name,
                _external=False,
                _scheme=scheme,
            ),
            'highest_version': {
                'href': url_for(
                    ".version",
                    namespace=colgroup.latest.namespace,
                    collection=colgroup.latest.name,
                    version=colgroup.latest.version,
                    _external=False,
                    _scheme=scheme,
                ),
                "version": colgroup.latest.version,
            },
        }
        results.append(result)

    this_url = url_for(
        ".collections",
        _external=False,
        _scheme=scheme,
        **request.args
    )

    out = {
        'meta': {
            'count': len(results),
        },
        'links': { # FIXME
            'first': this_url,
            'previous': None,
            'next': None,
            'last': this_url,
        },
        'data': results,
    }

    return out


@v3.route('/collections/<namespace>/<collection>')
@v3.route('/collections/<namespace>/<collection>/')
@v3.route('/plugin/ansible/content/published/collections/index/<namespace>/<collection>')
@v3.route('/plugin/ansible/content/published/collections/index/<namespace>/<collection>/', endpoint='collection')
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

    colcol = CollectionCollection.from_collections(discover_collections(repo=repository, namespace=namespace, name=collection))


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
                upstream_version = VersionInfo.parse(upstream_result['highest_version']['version'])
            except (KeyError, ValueError):
                # TODO: warn?
                pass
            else:
                if colgroup.latest < upstream_version:
                    return upstream_result

    result = {
        'href': url_for(
            ".collection",
            namespace=colgroup.namespace,
            collection=colgroup.name,
            _external=False,
            _scheme=scheme
        ),
        'name': colgroup.latest.name,
        'namespace': colgroup.latest.namespace,
        'deprecated': False, # FIXME
        'created_at': colgroup.latest.created,
        'updated_at': colgroup.latest.modified,
        'versions_url': url_for(
            ".versions",
            namespace=colgroup.latest.namespace,
            collection=colgroup.latest.name,
            _external=False,
            _scheme=scheme,
        ),
        'highest_version': {
            'href': url_for(
                ".version",
                namespace=colgroup.latest.namespace,
                collection=colgroup.latest.name,
                version=colgroup.latest.version,
                _external=False,
                _scheme=scheme,
            ),
            "version": colgroup.latest.version,
        },
    }
    return result

@v3.route('/collections/<namespace>/<collection>/versions')
@v3.route('/collections/<namespace>/<collection>/versions/')
@v3.route('/plugin/ansible/content/published/collections/index/<namespace>/<collection>/versions')
@v3.route('/plugin/ansible/content/published/collections/index/<namespace>/<collection>/versions/', endpoint='versions')
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

    collections = CollectionCollection.from_collections(discover_collections(repo=repository, namespace=namespace, name=collection))

    if not (collections or upstream_result):
        abort(C.HTTP_NOT_FOUND)

    if len(collections) > 1:
        abort(C.HTTP_INTERNAL_SERVER_ERROR)

    col = next(iter(collections.values()))
    vers = set()
    for i in col.values():
        results.append(
            {
                'href': url_for(
                    ".version",
                    namespace=i.namespace,
                    collection=i.name,
                    version=i.version,
                    _external=False,
                    _scheme=scheme,
                ),
                'version': i.version,
                'created_at': i.created,
                'updated_at': i.modified,
                'marks': [],
                'requires_ansible': None, # FIXME
            }
        )
        vers.add(i.version)

    if upstream_result:
        for item in upstream_result['data']:
            if item['version'] not in vers:
                results.append(item)

    this_url = url_for(
        ".versions",
        namespace=namespace,
        collection=collection,
        _external=False,
        _scheme=scheme,
        **request.args
    )

    out = {
        'meta': {
            'count': len(results),
        },
        'links': { # FIXME
            'first': this_url,
            'previous': None,
            'next': None,
            'last': this_url,
        },
        'data': results,
    }

    return out


@v3.route('/collections/<namespace>/<collection>/versions/<version>')
@v3.route('/collections/<namespace>/<collection>/versions/<version>/')
@v3.route('/plugin/ansible/content/published/collections/index/<namespace>/<collection>/versions/<version>')
@v3.route('/plugin/ansible/content/published/collections/index/<namespace>/<collection>/versions/<version>/', endpoint='version')
def version(namespace, collection, version):
    repository = authorize(request, current_app.config['ARTIFACTORY_PATH'])
    upstream = current_app.config['PROXY_UPSTREAM']
    no_proxy = current_app.config['NO_PROXY_NAMESPACES']
    cache_minutes = current_app.config['CACHE_MINUTES']
    cache_read = current_app.config['CACHE_READ']
    cache_write = current_app.config['CACHE_WRITE']
    scheme = current_app.config.get('PREFERRED_URL_SCHEME')

    try:
        info = next(discover_collections(repository, namespace=namespace, name=collection, version=version))
    except StopIteration:
        if upstream and (not no_proxy or namespace not in no_proxy):
            proxy = ProxyUpstream(repository, upstream, cache_read, cache_write, cache_minutes)
            upstream_result = proxy.proxy(request)
            upstream_result['download_url'] = url_for(
                'download.download',
                filename=upstream_result['artifact']['filename'],
                _external=True,
                _scheme=scheme,
                **{C.QUERY_DOWNLOAD_UPSTREAM_URL: upstream_result['download_url']},
            )
            return upstream_result
        else:
            abort(C.HTTP_NOT_FOUND)

    out = {
        'artifact': {
            'filename': info.filename,
            'sha256': info.sha256,
            'size': info.size,
        },
        'collection': {
            'href': url_for(
                ".collection",
                namespace=info.namespace,
                collection=info.name,
                _external=False,
                _scheme=scheme,
            ),
            'name': info.name,
        },
        'namespace': {
            'name': info.namespace,
        },
        'download_url': url_for(
            'download.download',
            filename=info.filename,
            _external=True,
            _scheme=scheme,
        ),
        'name': info.name,
        'signatures': [],
        'hidden': False,
        'href': url_for(
            ".collection",
            namespace=info.namespace,
            collection=info.name,
            _external=False,
            _scheme=scheme
        ),
        'id': 0,
        'metadata': info.collection_info,
        'version': info.version,
        'created_at': info.created,
        'updated_at': info.modified,
        'requires_ansible': None, # FIXME
        'marks': [],
    }
    return out


# not going to preserve the v2 paths for uploading
# @v3.route('/collections', methods=['POST'])
# @v3.route('/collections/', methods=['POST'])
@v3.route('/artifacts/collections', methods=['POST'])
@v3.route('/artifacts/collections/', methods=['POST'], endpoint='publish')
def publish():
    sha256 = request.form['sha256']
    file = request.files['file']
    skip_configured_auth = current_app.config['PUBLISH_SKIP_CONFIGURED_AUTH']
    property_fallback = current_app.config.get('USE_PROPERTY_FALLBACK', False)
    upload_format = current_app.config.get('UPLOAD_FORMAT')
    _scheme = current_app.config.get('PREFERRED_URL_SCHEME')

    target = authorize(request, current_app.config['ARTIFACTORY_PATH'] / file.filename, skip_configured_auth=skip_configured_auth)

    with _chunk_to_temp(IncomingCollectionStream(file, format=upload_format)) as tmp:
        if tmp.sha256 != sha256:
            abort(Response(f"Hash mismatch: uploaded=='{sha256}', calculated=='{tmp.sha256}'", C.HTTP_INTERNAL_SERVER_ERROR))

        upload_collection_from_hashed_tempfile(target, tmp, property_fallback=property_fallback)

    return jsonify(task=url_for(".import_singleton", _external=False, _scheme=_scheme))
