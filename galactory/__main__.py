# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

import logging
from configargparse import ArgParser
from artifactory import ArtifactoryPath

from . import create_app


if __name__ == '__main__':
    parser = ArgParser(
        prog='python -m galactory',
        description=(
            'galactory is a partial Ansible Galaxy proxy that uploads and downloads collections, '
            'using an Artifactory generic repository as its backend.'
        ),
        default_config_files=['/etc/galactory.d/*.conf', '~/.galactory/*.conf'],
    )
    parser.add_argument('-c', '--config', required=False, is_config_file=True, help='The path to a config file.')
    parser.add_argument('--listen-addr', default='0.0.0.0', type=str, env_var='GALACTORY_LISTEN_ADDR', help='The IP address to listen on.')
    parser.add_argument('--listen-port', default=5555, type=int, env_var='GALACTORY_LISTEN_PORT', help='The TCP port to listen on.')
    parser.add_argument('--server-name', type=str, env_var='GALACTORY_SERVER_NAME', help='The host name and port of the server, as seen from clients. Used for generating links.')
    parser.add_argument('--artifactory-path', type=str, required=True, env_var='GALACTORY_ARTIFACTORY_PATH', help='The URL of the path in Artifactory where collections are stored.')
    parser.add_argument('--artifactory-api-key', type=str, env_var='GALACTORY_ARTIFACTORY_API_KEY', help='If set, is the API key used to access Artifactory.')
    parser.add_argument('--use-galaxy-key', action='store_true', env_var='GALACTORY_USE_GALAXY_KEY', help='If set, uses the Galaxy token as the Artifactory API key.')
    parser.add_argument('--prefer-configured-key', action='store_true', env_var='GALACTORY_PREFER_CONFIGURED_KEY', help='If set, prefer the confgured Artifactory key over the Galaxy token.')
    parser.add_argument('--log-file', type=str, env_var='GALACTORY_LOG_FILE', help='If set, logging will go to this file instead of the console.')
    parser.add_argument(
        '--log-level',
        type=str.upper,
        env_var='GALACTORY_LOG_LEVEL',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='The desired logging level.',
    )
    parser.add_argument('--log-headers', action='store_true', env_var='GALACTORY_LOG_HEADERS', help='Log the headers of every request (DEBUG level only).')
    parser.add_argument('--log-body', action='store_true', env_var='GALACTORY_LOG_BODY', help='Log the body of every request (DEBUG level only).')
    parser.add_argument('--proxy-upstream', type=lambda x: str(x).rstrip('/') + '/', env_var='GALACTORY_PROXY_UPSTREAM', help='If set, then find, pull and cache results from the specified galaxy server in addition to local.')
    parser.add_argument('-npns', '--no-proxy-namespace', action='append', default=[], env_var='GALACTORY_NO_PROXY_NAMESPACE', help='Requests for this namespace should never be proxied. Can be specified multiple times.')
    args = parser.parse_args()

    logging.basicConfig(filename=args.log_file, level=args.log_level)

    app = create_app(
        ARTIFACTORY_PATH=ArtifactoryPath(args.artifactory_path),
        LOG_HEADERS=args.log_headers,
        LOG_BODY=args.log_body,
        PROXY_UPSTREAM=args.proxy_upstream,
        NO_PROXY_NAMESPACES=args.no_proxy_namespace,
        ARTIFACTORY_API_KEY=args.artifactory_api_key,
        USE_GALAXY_KEY=args.use_galaxy_key,
        PREFER_CONFIGURED_KEY=args.prefer_configured_key,
        SERVER_NAME=args.server_name,
    )

    print(app.url_map)
    app.run(args.listen_addr, args.listen_port, threaded=True)
