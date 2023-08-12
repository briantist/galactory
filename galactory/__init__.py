# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

import logging
import warnings

from flask import Flask, request
from werkzeug.middleware.proxy_fix import ProxyFix
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


def create_configured_app(run=False, parse_known_only=True, parse_allow_abbrev=False, proxy_fix=False, **extra):
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
    parser.add_argument('--artifactory-api-key', type=str, env_var='GALACTORY_ARTIFACTORY_API_KEY', help='If set, is the API key used to access Artifactory. If set with artifactory-access-token, this value will not be used.')
    parser.add_argument('--artifactory-access-token', type=str, env_var='GALACTORY_ARTIFACTORY_ACCESS_TOKEN', help='If set, is the Access Token used to access Artifactory. If set with artifactory-api-key, this value will be used and the API key will be ignored.')
    parser.add_argument('--use-galaxy-key', action='store_true', env_var='GALACTORY_USE_GALAXY_KEY', help='If set, uses the Galaxy token sent in the request as the Artifactory auth. DEPRECATED: This option will be removed in v0.11.0. Please use --use-galaxy-auth going forward.')
    parser.add_argument('--use-galaxy-auth', action='store_true', env_var='GALACTORY_USE_GALAXY_AUTH', help='If set, uses the Galaxy token sent in the request as the Artifactory auth.')
    parser.add_argument('--galaxy-auth-type', type=str, env_var='GALACTORY_GALAXY_AUTH_TYPE', choices=['api_key', 'access_token'], help='Auth received via a Galaxy request should be interpreted as this type of auth.')
    parser.add_argument('--prefer-configured-key', action='store_true', env_var='GALACTORY_PREFER_CONFIGURED_KEY', help='If set, prefer the confgured Artifactory auth over the Galaxy token. DEPRECATED: This option will be removed in v0.11.0. Please use --prefer-configured-auth going forward.')
    parser.add_argument('--prefer-configured-auth', action='store_true', env_var='GALACTORY_PREFER_CONFIGURED_AUTH', help='If set, prefer the confgured Artifactory auth over the Galaxy token.')
    parser.add_argument('--publish-skip-configured-key', action='store_true', env_var='GALACTORY_PUBLISH_SKIP_CONFIGURED_KEY', help='If set, publish endpoint will not use configured auth, only auth included in a Galaxy request. DEPRECATED: This option will be removed in v0.11.0. Please use --publish-skip-configured-auth going forward.')
    parser.add_argument('--publish-skip-configured-auth', action='store_true', env_var='GALACTORY_PUBLISH_SKIP_CONFIGURED_AUTH', help='If set, publish endpoint will not use configured auth, only auth included in a Galaxy request.')
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
    parser.add_argument('--cache-write', action=_StrBool, default=True, env_var='GALACTORY_CACHE_WRITE', help='Populate the upstream cache in Artifactory. Should be false when no auth is provided or the auth has no permission to write.')
    parser.add_argument('--use-property-fallback', action='store_true', env_var='GALACTORY_USE_PROPERTY_FALLBACK', help='Set properties of an uploaded collection in a separate request after publshinng. Requires a Pro license of Artifactory. This feature is a workaround for an Artifactory proxy configuration error and may be removed in a future version.')
    parser.add_argument('--health-check-custom-text', type=str, default='', env_var='GALACTORY_HEALTH_CHECK_CUSTOM_TEXT', help='Sets custom_text field for health check endpoint responses.')

    if parse_known_only:
        args, _ = parser.parse_known_args()
    else:
        args = parser.parse_args()

    logging.basicConfig(filename=args.log_file, level=args.log_level)

    # TODO: v0.11.0 - remove conditional old name
    if args.use_galaxy_key and not args.use_galaxy_auth:
        use_galaxy_auth = True
        warnings.warn(
            message=(
                "USE_GALAXY_KEY has been replaced by USE_GALAXY_AUTH and the old name will be removed in v0.11.0."
                " To suppress this warning, set USE_GALAXY_AUTH."
            ), category=DeprecationWarning, stacklevel=2
        )
    else:
        use_galaxy_auth = args.use_galaxy_auth

    # TODO: v0.11.0 - remove conditional & warning, set default on argument
    if args.galaxy_auth_type is None and use_galaxy_auth:
        galaxy_auth_type = 'api_key'
        warnings.warn(
            message=(
                "USE_GALAXY_AUTH is True but GALAXY_AUTH_TYPE is not set."
                " The default value used will be 'api_key' for backward compatibility, but will change to 'access_token' in v0.11.0."
                " To suppress this warning, set an explicit value."
            ), category=FutureWarning, stacklevel=2
        )
    else:
        galaxy_auth_type = args.galaxy_auth_type

    # TODO: v0.11.0 - remove conditional old name
    if args.prefer_configured_key and not args.prefer_configured_auth:
        prefer_configured_auth = True
        warnings.warn(
            message=(
                "PREFER_CONFIGURED_KEY has been replaced by PREFER_CONFIGURED_AUTH and the old name will be removed in v0.11.0."
                " To suppress this warning, set PREFER_CONFIGURED_AUTH."
            ), category=DeprecationWarning, stacklevel=2
        )
    else:
        prefer_configured_auth = args.prefer_configured_auth

    # TODO: v0.11.0 - remove conditional old name
    if args.publish_skip_configured_key and not args.publish_skip_configured_auth:
        publish_skip_configured_auth = True
        warnings.warn(
            message=(
                "PUBLISH_SKIP_CONFIGURED_KEY has been replaced by PUBLISH_SKIP_CONFIGURED_AUTH and the old name will be removed in v0.11.0."
                " To suppress this warning, set PUBLISH_SKIP_CONFIGURED_AUTH."
            ), category=DeprecationWarning, stacklevel=2
        )
    else:
        publish_skip_configured_auth = args.publish_skip_configured_auth

    app = create_app(
        ARTIFACTORY_PATH=ArtifactoryPath(args.artifactory_path),
        LOG_HEADERS=args.log_headers,
        LOG_BODY=args.log_body,
        PROXY_UPSTREAM=args.proxy_upstream,
        NO_PROXY_NAMESPACES=args.no_proxy_namespace,
        ARTIFACTORY_API_KEY=args.artifactory_api_key,
        ARTIFACTORY_ACCESS_TOKEN=args.artifactory_access_token,
        USE_GALAXY_AUTH=use_galaxy_auth,
        GALAXY_AUTH_TYPE=galaxy_auth_type,
        PREFER_CONFIGURED_AUTH=prefer_configured_auth,
        PUBLISH_SKIP_CONFIGURED_AUTH=publish_skip_configured_auth,
        SERVER_NAME=args.server_name,
        PREFERRED_URL_SCHEME=args.preferred_url_scheme,
        CACHE_MINUTES=args.cache_minutes,
        CACHE_READ=args.cache_read,
        CACHE_WRITE=args.cache_write,
        USE_PROPERTY_FALLBACK=args.use_property_fallback,
        HEALTH_CHECK_CUSTOM_TEXT=args.health_check_custom_text,
    )

    if proxy_fix:
        proxy_args = {k: v for k, v in extra.items() if k.startswith('x_')}
        app = ProxyFix(app, **proxy_args)

    if run:
        app.run(args.listen_addr, args.listen_port, threaded=True)

    return app
