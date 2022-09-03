# galactory
galactory is An Ansible Galaxy proxy for Artifactory.

Using an Artifactory Generic repository as its backend, galactory implements a limited subset of the Galaxy v2 API to allow for installing and publishing collections.

It can also be set up to transparently proxy an upstream Galaxy server, storing the pulled artifacts in Artifactory, to be served as local artifacts from then on. This helps avoid throttling errors on busy CI systems, and allows for internal/private collections to declare dependencies on upstream collections (dependencies will only be installed from the same Galaxy server where a collection was installed from).

# Acknowledgements
This project is _heavily_ inspired by [amanda](https://github.com/sivel/amanda/).

# How to use
There isn't any proper documentation yet. Here's the help output:

```text
usage: python -m galactory [-h] [--listen-addr LISTEN_ADDR] [--listen-port LISTEN_PORT] [--server-name SERVER_NAME]
                           --artifactory-path ARTIFACTORY_PATH [--artifactory-api-key ARTIFACTORY_API_KEY]
                           [--use-galaxy-key] [--prefer-configured-key] [--log-file LOG_FILE]
                           [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--log-headers] [--log-body]
                           [--proxy-upstream PROXY_UPSTREAM] [-npns NO_PROXY_NAMESPACE]

galactory is a partial Ansible Galaxy proxy that uploads and downloads collections, using an Artifactory generic
repository as its backend.

optional arguments:
  -h, --help            show this help message and exit
  --listen-addr LISTEN_ADDR
                        The IP address to listen on.
  --listen-port LISTEN_PORT
                        The TCP port to listen on.
  --server-name SERVER_NAME
                        The host name and port of the server, as seen from clients. Used for generating links.
  --artifactory-path ARTIFACTORY_PATH
                        The URL of the path in Artifactory where collections are stored.
  --artifactory-api-key ARTIFACTORY_API_KEY
                        If set, is the API key used to access Artifactory.
  --use-galaxy-key      If set, uses the Galaxy token as the Artifactory API key.
  --prefer-configured-key
                        If set, prefer the confgured Artifactory key over the Galaxy token.
  --log-file LOG_FILE   If set, logging will go to this file instead of the console.
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The desired logging level.
  --log-headers         Log the headers of every request (DEBUG level only).
  --log-body            Log the body of every request (DEBUG level only).
  --proxy-upstream PROXY_UPSTREAM
                        If set, then find, pull and cache results from the specified galaxy server in addition to
                        local.
  -npns NO_PROXY_NAMESPACE, --no-proxy-namespace NO_PROXY_NAMESPACE
                        Requests for this namespace should never be proxied. Can be specified multiple times.
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
