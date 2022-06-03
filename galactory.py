#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

import json
import semver
import logging

from datetime import datetime
from base64io import Base64IO
from argparse import ArgumentParser

from urllib.request import urlopen

from flask import Flask, abort, url_for, request, Response

from artifactory import ArtifactoryPath, ArtifactoryException

CONTENT_TYPE = {'Content-Type': 'application/json'}
HTTP_OK = 200
HTTP_NOT_FOUND = 404
HTTP_INTERNAL_SERVER_ERROR = 500

API_RESPONSE = json.dumps(
    {
        'available_versions': {
            'v2': 'v2/',
        },
        'current_version': 'v2',
        'description': 'GALAXY REST API',
    },
)


app = Flask(__name__)


@app.route('/api')
@app.route('/api/')
def api():
    return (API_RESPONSE, HTTP_OK, CONTENT_TYPE)


def load_manifest_from_artifactory(artifact):
    with urlopen(str(artifact) + '!/MANIFEST.json') as u:
        manifest = json.load(u)
    return manifest


def discover_collections(repo, namespace=None, name=None, version=None):
    for p in repo:
        props = p.properties
        info = p.stat()

        if info.is_dir or not props['version']:
            continue

        manifest = load_manifest_from_artifactory(p)

        coldata = {
            'collection_info': manifest['collection_info'],
            'fqcn': props['fqcn'][0],
            'created': info.ctime.isoformat(),
            'modified': info.mtime.isoformat(),
            'namespace': {'name': props['namespace'][0]},
            'name': props['name'][0],
            'filename': p.name,
            'sha256': info.sha256,
            'size': info.size,
            'download_url': str(p),
            'mime_type': info.mime_type,
            'version': props['version'][0],
            'semver': semver.VersionInfo.parse(props['version'][0]),
        }

        if all(
            (
                not namespace or coldata['namespace']['name'] == namespace,
                not name or coldata['name'] == name,
                not version or coldata['version'] == version
            )
        ):
            yield coldata


def collected_collections(repo, namespace=None, name=None):
    collections = {}

    for c in discover_collections(repo, namespace=namespace, name=name):
        version = c['version']
        ver = c['semver']
        col = collections.setdefault(c['fqcn'], {})
        versions = col.setdefault('versions', {})
        versions[version] = c
        if not ver.prerelease:
            try:
                latest = col['latest']
            except KeyError:
                col['latest'] = c
            else:
                if ver > latest['semver']:
                    col['latest'] = c

    return collections



def _collection_listing(repo, namespace=None, collection=None):
    collections = collected_collections(repo, namespace, collection)

    results = []

    for _, i in collections.items():
        latest = i['latest']

        result = {
            'href': request.url,
            'name': latest['name'],
            'namespace': latest['namespace'],
            'created': latest['created'],
            'modified': latest['modified'],
            'versions_url': url_for(
                'versions',
                namespace=latest['namespace']['name'],
                collection=latest['name'],
                _external=True,
            ),
            'latest_version': {
                'href': url_for(
                    'version',
                    namespace=latest['namespace']['name'],
                    collection=latest['name'],
                    version=latest['version'],
                    _external=True,
                ),
                "version": latest['version'],
            }
        }
        results.append(result)

    return results


@app.route('/api/v2/collections')
@app.route('/api/v2/collections/')
def collections():
    results = _collection_listing(app.config['ARTIFACTORY_PATH'])
    return json.dumps({'results': results}, default=str), HTTP_OK, CONTENT_TYPE


@app.route('/api/v2/collections/<namespace>/<collection>')
@app.route('/api/v2/collections/<namespace>/<collection>/')
def collection(namespace, collection):
    results = _collection_listing(app.config['ARTIFACTORY_PATH'], namespace, collection)
    return json.dumps(results[0], default=str), HTTP_OK, CONTENT_TYPE


@app.route('/api/v2/collections/<namespace>/<collection>/versions')
@app.route('/api/v2/collections/<namespace>/<collection>/versions/')
def versions(namespace, collection):
    results = []
    collections = collected_collections(app.config['ARTIFACTORY_PATH'], namespace=namespace, name=collection)

    if not collections:
        abort(HTTP_NOT_FOUND)

    if len(collections) > 1:
        abort(HTTP_INTERNAL_SERVER_ERROR)

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
    return json.dumps(out, default=str), HTTP_OK, CONTENT_TYPE


@app.route('/api/v2/collections/<namespace>/<collection>/versions/<version>')
@app.route('/api/v2/collections/<namespace>/<collection>/versions/<version>/')
def version(namespace, collection, version):
    try:
        info = next(discover_collections(app.config['ARTIFACTORY_PATH'], namespace=namespace, name=collection, version=version))
    except StopIteration:
        abort(HTTP_NOT_FOUND)

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

    return json.dumps(out, default=str), HTTP_OK, CONTENT_TYPE


@app.route('/api/v2/collections', methods=['POST'])
@app.route('/api/v2/collections/', methods=['POST'])
def publish():
    sha256 = request.form['sha256']
    file = request.files['file']
    token = None
    authorization = request.headers.get('Authorization')
    if authorization:
        token = authorization.split(' ')[1]

    target = app.config['ARTIFACTORY_PATH'] / file.filename

    if token:
        target = ArtifactoryPath(target, apikey=token)

    decoded = Base64IO(file)

    try:
        target.deploy(decoded, sha256=sha256)
    except ArtifactoryException as exc:
        cause = exc.__cause__
        app.logger.debug(cause)
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

    out = {
        'task': url_for('ok', _external=True),
    }

    return json.dumps(out), HTTP_OK, CONTENT_TYPE


# TODO: optionally proxy the download from artifactory
# will be useful if repo requires authentication to download
# @app.route('/api/v2/collections/download/<filename>')
# def download(filename):
#     pass


@app.route('/api/v2/collection-imports/0')
@app.route('/api/v2/collection-imports/0/')
def ok():
    out = {
        'state': 'completed',
        'finished_at': datetime.utcnow().isoformat(),
    }
    return json.dumps(out), HTTP_OK, CONTENT_TYPE


@app.before_request
def log():
    if app.config['LOG_HEADERS']:
        app.logger.debug('Headers: %s', request.headers)

    if app.config['LOG_BODY']:
        app.logger.debug('Body: %s', request.get_data())


if __name__ == '__main__':
    parser = ArgumentParser(
        description=(
            'galactory is a partial Ansible Galaxy proxy that uploads and downloads collections, '
            'using an Artifactory generic repository as its backend.'
        )
    )
    parser.add_argument('--listen-addr', default='0.0.0.0', type=str, help='The IP address to listen on.')
    parser.add_argument('--listen-port', default=5555, type=int, help='The TCP port to listen on.')
    parser.add_argument('--artifactory-path', type=str, required=True, help='The URL of the path in Artifactory where collections are stored.')
    parser.add_argument('--log-file', type=str, help='If set, logging will go to this file instead of the console.')
    parser.add_argument(
        '--log-level',
        type=str.upper,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='The desired logging level.',
    )
    parser.add_argument('--log-headers', action='store_true', help='Log the headers of every request (DEBUG level only).')
    parser.add_argument('--log-body', action='store_true', help='Log the body of every request (DEBUG level only).')
    args = parser.parse_args()

    logging.basicConfig(filename=args.log_file, level=args.log_level)

    app.config.update(
        ARTIFACTORY_PATH=ArtifactoryPath(args.artifactory_path),
        LOG_HEADERS=args.log_headers,
        LOG_BODY=args.log_body,
    )
    app.run(args.listen_addr, args.listen_port, threaded=True)
