# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

import json

from flask import abort, request, current_app, send_file, Response
from artifactory import ArtifactoryException

from . import bp as dl
from .. import constants as C
from ..utilities import load_manifest_from_artifactory, authorize, _chunk_to_temp
from ..upstream import ProxyUpstream


@dl.route('/<filename>')
def download(filename):
    artifact = authorize(request, current_app.config['ARTIFACTORY_PATH'] / filename)
    upstream = current_app.config['PROXY_UPSTREAM']
    # no_proxy = current_app.config['NO_PROXY_NAMESPACES']
    cache_minutes = current_app.config['CACHE_MINUTES']
    cache_read = current_app.config['CACHE_READ']
    cache_write = current_app.config['CACHE_WRITE']

    try:
        stat = artifact.stat()
    except FileNotFoundError:
        # Although there's a naming convention for the collection tarballs, the name is not actually
        # at all significant for the download/install process; previous API calls gave the download
        # URL exactly. So we don't actually have namespace information to check for no-proxying.
        # TODO: consider whether we should filter by the naming convention, maybe configurable.
        if not upstream:  # or not (not no_proxy or namespace not in no_proxy):
            abort(C.HTTP_NOT_FOUND)

        proxy = ProxyUpstream(artifact, upstream, cache_read, cache_write, cache_minutes)

        with proxy.proxy_download(request) as resp, _chunk_to_temp(None, iterator=resp.iter_content, close=cache_write) as tmp:
            if not cache_write:
                return send_file(tmp.handle, as_attachment=True, download_name=filename, etag=False)

            try:
                artifact.deploy(tmp.handle, md5=tmp.md5, sha1=tmp.sha1, sha256=tmp.sha256)
            except ArtifactoryException as exc:
                cause = exc.__cause__
                current_app.logger.debug(cause)
                abort(Response(cause.response.text, cause.response.status_code))
            else:
                manifest = load_manifest_from_artifactory(artifact)
                ci = manifest['collection_info']
                props = {
                    'collection_info': json.dumps(ci),
                    'namespace': ci['namespace'],
                    'name': ci['name'],
                    'version': ci['version'],
                    'fqcn': f"{ci['namespace']}.{ci['name']}"
                }
                artifact.properties = props
                stat = artifact.stat()

    return send_file(artifact.open(), as_attachment=True, download_name=artifact.name, last_modified=stat.mtime, etag=False)
