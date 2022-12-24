[![Test](https://github.com/briantist/galactory/actions/workflows/test.yml/badge.svg)](https://github.com/briantist/galactory/actions/workflows/test.yml) [![codecov](https://codecov.io/gh/briantist/galactory/branch/main/graph/badge.svg?token=5ZS2WXM4K9)](https://codecov.io/gh/briantist/galactory)

# galactory
galactory is An Ansible Galaxy proxy for Artifactory.

Using an Artifactory Generic repository as its backend, galactory implements a limited subset of the Galaxy v2 API to allow for installing and publishing collections.

It can also be set up to transparently proxy an upstream Galaxy server, storing the pulled artifacts in Artifactory, to be served as local artifacts from then on. This helps avoid throttling errors on busy CI systems, and allows for internal/private collections to declare dependencies on upstream collections (dependencies will only be installed from the same Galaxy server where a collection was installed from).

# Acknowledgements
This project is _heavily_ inspired by [amanda](https://github.com/sivel/amanda/).

# Artifactory compatibility
For the time being some features may require an Artifactory Pro license. Work is being done to workaround the (many) limitations that JFrog has placed on API calls. [These limitations have also complicated the ability to run integration tests](https://github.com/briantist/galactory/issues/6). As a result, the test of whether all Pro license dependent API calls have been rooted out, will be whether test coverage exists that can run against Artifactory OSS.

# How to use
There isn't any proper documentation yet. The help output is below.

Pulling out this bit about configuration for emphasis:

> Args that start with `--` (eg. `--listen-addr`) can also be set in a config file (`/etc/galactory.d/*.conf` or `~/.galactory/*.conf` or specified via `-c`). Config file syntax allows:
> - `key=value`
> - `flag=true`
> - `stuff=[a,b,c]`
> (for details, see `DefaultConfigFileParser` syntax at https://github.com/bw2/ConfigArgParse#config-file-syntax).
>
> If an arg is specified in more than one place, then commandline values override environment variables which override config file values which override defaults.
>
> `defaults < config < environment variables < command line` (last one found wins)

```text
usage: python -m galactory [-h] [-c CONFIG] [--listen-addr LISTEN_ADDR]
                           [--listen-port LISTEN_PORT] [--server-name SERVER_NAME]
                           [--preferred-url-scheme PREFERRED_URL_SCHEME]
                           --artifactory-path ARTIFACTORY_PATH
                           [--artifactory-api-key ARTIFACTORY_API_KEY] [--use-galaxy-key]
                           [--prefer-configured-key] [--publish-skip-configured-key]
                           [--log-file LOG_FILE]
                           [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--log-headers]
                           [--log-body] [--proxy-upstream PROXY_UPSTREAM]
                           [-npns NO_PROXY_NAMESPACE] [--cache-minutes CACHE_MINUTES]
                           [--cache-read CACHE_READ] [--cache-write CACHE_WRITE]
                           [--use-property-fallback]
                           [--health-check-custom-text HEALTH_CHECK_CUSTOM_TEXT]

galactory is a partial Ansible Galaxy proxy that uploads and downloads collections, using an
Artifactory generic repository as its backend.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        The path to a config file. [env var: GALACTORY_CONFIG]
  --listen-addr LISTEN_ADDR
                        The IP address to listen on. [env var: GALACTORY_LISTEN_ADDR]
  --listen-port LISTEN_PORT
                        The TCP port to listen on. [env var: GALACTORY_LISTEN_PORT]
  --server-name SERVER_NAME
                        The host name and port of the server, as seen from clients. Used for
                        generating links. [env var: GALACTORY_SERVER_NAME]
  --preferred-url-scheme PREFERRED_URL_SCHEME
                        Sets the preferred scheme to use when constructing URLs. Defaults to
                        the request scheme, but is unaware of reverse proxies.
                        [env var: GALACTORY_PREFERRED_URL_SCHEME]
  --artifactory-path ARTIFACTORY_PATH
                        The URL of the path in Artifactory where collections are stored.
                        [env var: GALACTORY_ARTIFACTORY_PATH]
  --artifactory-api-key ARTIFACTORY_API_KEY
                        If set, is the API key used to access Artifactory.
                        [env var: GALACTORY_ARTIFACTORY_API_KEY]
  --use-galaxy-key      If set, uses the Galaxy token as the Artifactory API key.
                        [env var: GALACTORY_USE_GALAXY_KEY]
  --prefer-configured-key
                        If set, prefer the confgured Artifactory key over the Galaxy token.
                        [env var: GALACTORY_PREFER_CONFIGURED_KEY]
 --publish-skip-configured-key
                        If set, publish endpoint will not use a configured key, only Galaxy token.
                        [env var: GALACTORY_PUBLISH_SKIP_CONFIGURED_KEY]
  --log-file LOG_FILE   If set, logging will go to this file instead of the console.
                        [env var: GALACTORY_LOG_FILE]
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The desired logging level. [env var: GALACTORY_LOG_LEVEL]
  --log-headers         Log the headers of every request (DEBUG level only).
                        [env var: GALACTORY_LOG_HEADERS]
  --log-body            Log the body of every request (DEBUG level only).
                        [env var: GALACTORY_LOG_BODY]
  --proxy-upstream PROXY_UPSTREAM
                        If set, then find, pull and cache results from the specified galaxy server
                        in addition to local. [env var: GALACTORY_PROXY_UPSTREAM]
  -npns NO_PROXY_NAMESPACE, --no-proxy-namespace NO_PROXY_NAMESPACE
                        Requests for this namespace should never be proxied. Can be specified
                        multiple times. [env var: GALACTORY_NO_PROXY_NAMESPACE]
  --cache-minutes CACHE_MINUTES
                        The time period that a cache entry should be considered valid.
                        [env var: GALACTORY_CACHE_MINUTES]
  --cache-read CACHE_READ
                        Look for upsteam caches and use their values.
                        [env var: GALACTORY_CACHE_READ]
  --cache-write CACHE_WRITE
                        Populate the upstream cache in Artifactory. Should be false when no API key is
                        provided or the key has no permission to write.
                        [env var: GALACTORY_CACHE_WRITE]
  --use-property-fallback
                        Set properties of an uploaded collection in a separate request after publshinng.
                        Requires a Pro license of Artifactory. This feature is a workaround for an
                        Artifactory proxy configuration error and may be removed in a future version.
                        [env var: GALACTORY_USE_PROPERTY_FALLBACK]
  --health-check-custom-text HEALTH_CHECK_CUSTOM_TEXT
                        Sets custom_text field for health check endpoint responses.
                        [env var: GALACTORY_HEALTH_CHECK_CUSTOM_TEXT]

Args that start with '--' (eg. --listen-addr) can also be set in a config file
(/etc/galactory.d/*.conf or ~/.galactory/*.conf or specified via -c). Config file syntax allows:
key=value, flag=true, stuff=[a,b,c] (for details, see syntax at https://goo.gl/R74nmi). If an arg
is specified in more than one place, then commandline values override environment variables which
override config file values which override defaults.
```

## Install
```shell
python3 -m pip install galactory
```

## Container

Latest tagged release:
```shell
docker run --rm ghcr.io/briantist/galactory:latest --help
```

Latest commit on `main`:
```shell
docker run --rm ghcr.io/briantist/galactory:main --help
```
