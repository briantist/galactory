# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

from base64io import Base64IO
from artifactory import ArtifactoryPath, ArtifactoryException
from flask import Response, jsonify, abort, url_for, request, current_app

from . import bp as v2
from ... import constants as C
from ...utilities import (
    discover_collections,
    collected_collections,
    _collection_listing,
    load_manifest_from_artifactory,
    authorize,
)


@v2.route('/collections')
@v2.route('/collections/')
def collections():
    results = _collection_listing(current_app.config['ARTIFACTORY_PATH'])
    return jsonify(results=results)


@v2.route('/collections/<namespace>/<collection>')
@v2.route('/collections/<namespace>/<collection>/')
def collection(namespace, collection):
    repository = authorize(request, current_app.config['ARTIFACTORY_PATH'])
    results = _collection_listing(repository, namespace, collection)
    return jsonify(results[0])


@v2.route('/collections/<namespace>/<collection>/versions')
@v2.route('/collections/<namespace>/<collection>/versions/')
def versions(namespace, collection):
    results = []
    repository = authorize(request, current_app.config['ARTIFACTORY_PATH'])

    collections = collected_collections(repository, namespace=namespace, name=collection)
    if not collections:
        abort(C.HTTP_NOT_FOUND)

    if len(collections) > 1:
        abort(C.HTTP_INTERNAL_SERVER_ERROR)

    for _, c in collections.items():
        for v, i in c['versions'].items():
            results.append(
                {
                    'href': url_for(
                        'version',
                        namespace=i['namespace']['name'],
                        collection=i['name'],
                        version=v,
                        _external=True,
                    ),
                    'version': v,
                }
            )

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
    try:
        info = next(discover_collections(repository, namespace=namespace, name=collection, version=version))
    except StopIteration:
        abort(C.HTTP_NOT_FOUND)

    out = {
        'artifact': {
            'filename': info['filename'],
            'sha256': info['sha256'],
            'size': info['size'],
        },
        'collection': {
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

    target = authorize(request, current_app.config['ARTIFACTORY_PATH'] / file.filename)

    decoded = Base64IO(file)

    try:
        target.deploy(decoded, sha256=sha256)
    except ArtifactoryException as exc:
        cause = exc.__cause__
        current_app.logger.debug(cause)
        abort(Response(cause.response.text, cause.response.status_code))
    else:
        manifest = load_manifest_from_artifactory(target)
        ci = manifest['collection_info']
        props = {
            'namespace': ci['namespace'],
            'name': ci['name'],
            'version': ci['version'],
            'fqcn': f"{ci['namespace']}.{ci['name']}"
        }
        target.properties = props

    return jsonify(task=url_for('import_singleton', _external=True))


# TODO: optionally proxy the download from artifactory
# will be useful if repo requires authentication to download
# @app.route('/collections/download/<filename>')
# def download(filename):
#     pass
