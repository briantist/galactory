#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

import logging
from argparse import ArgumentParser
from artifactory import ArtifactoryPath

from galactory import create_app


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

    app = create_app()

    app.config.update(
        ARTIFACTORY_PATH=ArtifactoryPath(args.artifactory_path),
        LOG_HEADERS=args.log_headers,
        LOG_BODY=args.log_body,
    )
    print(app.url_map)
    app.run(args.listen_addr, args.listen_port, threaded=True)
