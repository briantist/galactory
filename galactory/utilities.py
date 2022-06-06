# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

import json
import semver

from urllib.request import urlopen

from flask import url_for, request


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
