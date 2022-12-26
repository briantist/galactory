# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

import logging

from flask import Flask, request
from configargparse import ArgParser, ArgumentError, Action
from artifactory import ArtifactoryPath

from .utilities import DateTimeIsoFormatJSONProvider

from .api import bp as api
from .download import bp as download
from .health import bp as health
from .root import bp as root

def create_app(**config):
    app = Flask(__name__)
    app.json = DateTimeIsoFormatJSONProvider(app)
    app.config.update(**config)
    app.register_blueprint(health)
    app.register_blueprint(root)
    app.register_blueprint(api)
    app.register_blueprint(download)

    @app.before_request
    def log():
        if app.config.get('LOG_HEADERS'):
            app.logger.debug('Headers: %s', request.headers)

        if app.config.get('LOG_BODY'):
            app.logger.debug('Body: %s', request.get_data())

    return app


# TODO: when py3.8 support is dropped, switch to using argparse.BooleanOptionalAction
class _StrBool(Action):
    FALSES = {'false', '0', 'no'}
    TRUES = {'true', '1', 'yes'}

    def _booler(self, value):
        if isinstance(value, bool):
            return value

        if value.lower() in self.FALSES:
            return False
        if value.lower() in self.TRUES:
            return True

        raise ArgumentError(self, f"Expecting 'true', 'false', 'yes', 'no', '1' or '0', but got '{value}'")

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, self._booler(values))


def create_configured_app(run=False, parse_known_only=True, parse_allow_abbrev=False):
    parser = ArgParser(
        prog='python -m galactory',
        description=(
            'galactory is a partial Ansible Galaxy proxy that uploads and downloads collections, '
            'using an Artifactory generic repository as its backend.'
        ),
        default_config_files=['/etc/galactory.d/*.conf', '~/.galactory/*.conf'],
        allow_abbrev=parse_allow_abbrev,
    )
    parser.add_argument('-c', '--config', required=False, is_config_file=True, env_var='GALACTORY_CONFIG', help='The path to a config file.')
    parser.add_argument('--listen-addr', default='0.0.0.0', type=str, env_var='GALACTORY_LISTEN_ADDR', help='The IP address to listen on.')
    parser.add_argument('--listen-port', default=5555, type=int, env_var='GALACTORY_LISTEN_PORT', help='The TCP port to listen on.')
    parser.add_argument('--server-name', type=str, env_var='GALACTORY_SERVER_NAME', help='The host name and port of the server, as seen from clients. Used for generating links.')
    parser.add_argument('--preferred-url-scheme', type=str, env_var='GALACTORY_PREFERRED_URL_SCHEME', help='Sets the preferred scheme to use when constructing URLs. Defaults to the request scheme, but is unaware of reverse proxies.')
    parser.add_argument('--artifactory-path', type=str, required=True, env_var='GALACTORY_ARTIFACTORY_PATH', help='The URL of the path in Artifactory where collections are stored.')
    parser.add_argument('--artifactory-api-key', type=str, env_var='GALACTORY_ARTIFACTORY_API_KEY', help='If set, is the API key used to access Artifactory.')
    parser.add_argument('--use-galaxy-key', action='store_true', env_var='GALACTORY_USE_GALAXY_KEY', help='If set, uses the Galaxy token as the Artifactory API key.')
    parser.add_argument('--prefer-configured-key', action='store_true', env_var='GALACTORY_PREFER_CONFIGURED_KEY', help='If set, prefer the confgured Artifactory key over the Galaxy token.')
    parser.add_argument('--publish-skip-configured-key', action='store_true', env_var='GALACTORY_PUBLISH_SKIP_CONFIGURED_KEY', help='If set, publish endpoint will not use a configured key, only Galaxy token.')
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
    parser.add_argument('--cache-minutes', default=60, type=int, env_var='GALACTORY_CACHE_MINUTES', help='The time period that a cache entry should be considered valid.')
    parser.add_argument('--cache-read', action=_StrBool, default=True, env_var='GALACTORY_CACHE_READ', help='Look for upsteam caches and use their values.')
    parser.add_argument('--cache-write', action=_StrBool, default=True, env_var='GALACTORY_CACHE_WRITE', help='Populate the upstream cache in Artifactory. Should be false when no API key is provided or the key has no permission to write.')
    parser.add_argument('--use-property-fallback', action='store_true', env_var='GALACTORY_USE_PROPERTY_FALLBACK', help='Set properties of an uploaded collection in a separate request after publshinng. Requires a Pro license of Artifactory. This feature is a workaround for an Artifactory proxy configuration error and may be removed in a future version.')
    parser.add_argument('--health-check-custom-text', type=str, default='', env_var='GALACTORY_HEALTH_CHECK_CUSTOM_TEXT', help='Sets custom_text field for health check endpoint responses.')

    if parse_known_only:
        args, _ = parser.parse_known_args()
    else:
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
        PUBLISH_SKIP_CONFIGURED_KEY=args.publish_skip_configured_key,
        SERVER_NAME=args.server_name,
        PREFERRED_URL_SCHEME=args.preferred_url_scheme,
        CACHE_MINUTES=args.cache_minutes,
        CACHE_READ=args.cache_read,
        CACHE_WRITE=args.cache_write,
        USE_PROPERTY_FALLBACK=args.use_property_fallback,
        HEALTH_CHECK_CUSTOM_TEXT=args.health_check_custom_text,
    )

    if run:
        app.run(args.listen_addr, args.listen_port, threaded=True)

    return app
