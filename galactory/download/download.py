# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

from flask import abort, request, current_app, send_file

from . import bp as dl
from .. import constants as C
from ..utilities import authorize, _chunk_to_temp, upload_collection_from_hashed_tempfile
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

            upload_collection_from_hashed_tempfile(artifact, tmp)

        stat = artifact.stat()

    return send_file(artifact.open(), as_attachment=True, download_name=artifact.name, last_modified=stat.mtime, etag=False)
