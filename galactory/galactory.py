#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

# import json
# import semver
# import logging

# from datetime import datetime
# from base64io import Base64IO
# from argparse import ArgumentParser

# from urllib.request import urlopen

# from flask import Flask, abort, url_for, request, Response

# from artifactory import ArtifactoryPath, ArtifactoryException

# from . import constants as C

# from .api import bp as api
# from .utilities import discover_collections, collected_collections, _collection_listing, load_manifest_from_artifactory

# app = Flask(__name__)

# app.register_blueprint(api)


# @app.route('/api/v2/collections')
# @app.route('/api/v2/collections/')
# def collections():
#     results = _collection_listing(app.config['ARTIFACTORY_PATH'])
#     return json.dumps({'results': results}, default=str), C.HTTP_OK, C.CONTENT_TYPE


# @app.route('/api/v2/collections/<namespace>/<collection>')
# @app.route('/api/v2/collections/<namespace>/<collection>/')
# def collection(namespace, collection):
#     results = _collection_listing(app.config['ARTIFACTORY_PATH'], namespace, collection)
#     return json.dumps(results[0], default=str), C.HTTP_OK, C.CONTENT_TYPE


# @app.route('/api/v2/collections/<namespace>/<collection>/versions')
# @app.route('/api/v2/collections/<namespace>/<collection>/versions/')
# def versions(namespace, collection):
#     results = []
#     collections = collected_collections(app.config['ARTIFACTORY_PATH'], namespace=namespace, name=collection)

#     if not collections:
#         abort(C.HTTP_NOT_FOUND)

#     if len(collections) > 1:
#         abort(C.HTTP_INTERNAL_SERVER_ERROR)

#     for _, c in collections.items():
#         for v, i in c['versions'].items():
#             results.append(
#                 {
#                     'href': url_for(
#                         'version',
#                         namespace=i['namespace']['name'],
#                         collection=i['name'],
#                         version=v,
#                         _external=True,
#                     ),
#                     'version': v,
#                 }
#             )

#     out = {
#         'count': len(results),
#         'next': None,
#         'previous': None,
#         'results': results,
#     }
#     return json.dumps(out, default=str), C.HTTP_OK, C.CONTENT_TYPE


# @app.route('/api/v2/collections/<namespace>/<collection>/versions/<version>')
# @app.route('/api/v2/collections/<namespace>/<collection>/versions/<version>/')
# def version(namespace, collection, version):
#     try:
#         info = next(discover_collections(app.config['ARTIFACTORY_PATH'], namespace=namespace, name=collection, version=version))
#     except StopIteration:
#         abort(C.HTTP_NOT_FOUND)

#     out = {
#         'artifact': {
#             'filename': info['filename'],
#             'sha256': info['sha256'],
#             'size': info['size'],
#         },
#         'collection': {
#             'name': info['name'],
#         },
#         'namespace': info['namespace'],
#         'download_url': info['download_url'],
#         'hidden': False,
#         'href': request.url,
#         'id': 0,
#         'metadata': info['collection_info'],
#         'version': version,
#     }

#     return json.dumps(out, default=str), C.HTTP_OK, C.CONTENT_TYPE


# @app.route('/api/v2/collections', methods=['POST'])
# @app.route('/api/v2/collections/', methods=['POST'])
# def publish():
#     sha256 = request.form['sha256']
#     file = request.files['file']
#     token = None
#     authorization = request.headers.get('Authorization')
#     if authorization:
#         token = authorization.split(' ')[1]

#     target = app.config['ARTIFACTORY_PATH'] / file.filename

#     if token:
#         target = ArtifactoryPath(target, apikey=token)

#     decoded = Base64IO(file)

#     try:
#         target.deploy(decoded, sha256=sha256)
#     except ArtifactoryException as exc:
#         cause = exc.__cause__
#         app.logger.debug(cause)
#         abort(Response(cause.response.text, cause.response.status_code))
#     else:
#         manifest = load_manifest_from_artifactory(target)
#         ci = manifest['collection_info']
#         props = {
#             'namespace': ci['namespace'],
#             'name': ci['name'],
#             'version': ci['version'],
#             'fqcn': f"{ci['namespace']}.{ci['name']}"
#         }
#         target.properties = props

#     out = {
#         'task': url_for('ok', _external=True),
#     }

#     return json.dumps(out), C.HTTP_OK, C.CONTENT_TYPE


# TODO: optionally proxy the download from artifactory
# will be useful if repo requires authentication to download
# @app.route('/api/v2/collections/download/<filename>')
# def download(filename):
#     pass


# @app.route('/api/v2/collection-imports/0')
# @app.route('/api/v2/collection-imports/0/')
# def ok():
#     out = {
#         'state': 'completed',
#         'finished_at': datetime.utcnow().isoformat(),
#     }
#     return json.dumps(out), C.HTTP_OK, C.CONTENT_TYPE


# @app.before_request
# def log():
#     if app.config.get('LOG_HEADERS'):
#         app.logger.debug('Headers: %s', request.headers)

#     if app.config.get('LOG_BODY'):
#         app.logger.debug('Body: %s', request.get_data())
