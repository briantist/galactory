=======================
galactory Release Notes
=======================

.. contents:: Topics


v0.8.0
======

Release Summary
---------------

This version is full of new features and bugfixes, and our first external contributor!

There's a new factory method that lets you re-use the same config system in place as the CLI without starting the internal web server, for use with a custom WSGI server, support for Brotli compression in upstreams, proper use of proxy environment variables, a new parameter to set a preferred URL scheme to help with reverse proxy use, and the first health check endpoint.

This release also removes use of a deprecated Flask feature (not user facing) and fixed the tests to work with Python 3.10 and 3.11, which we now test in CI.

Minor Changes
-------------

- WSGI support - in addition to the bare ``create_app`` factory function, there is now a ``create_configurd_app`` factory function, which uses the same argument parsing as running from the CLI; this allows for using an external WSGI server while taking advantage of the environment variables and configuration file support to set the configuration (https://github.com/briantist/galactory/pull/28).
- healthchecks - the first health check endpoint has been added, which can be used for load balancers, reverse proxies, smart DNS, and more (https://github.com/briantist/galactory/issues/30).
- upstream proxying - merge the ``requests`` environment for proxied requests so that environment variables such as ``REQUESTS_CA_BUNDLE`` are used appropriately (https://github.com/briantist/galactory/issues/25).

Bugfixes
--------

- generated URLs had no way to set the scheme for use reverse proxies or load balancers (https://github.com/briantist/galactory/issues/27).
- the ``/api/`` endpoint did not define a route that didn't end in ``/``, which caused Flask to issue a redirect, however the redirect does not use the preferred scheme (https://github.com/briantist/galactory/pull/29).
- the ``href`` field in responses did not use the new support for schemes (https://github.com/briantist/galactory/pull/29).
- the bare ``collections/`` endpoint was not using authorization and would have failed if authentication was required to read from Artifactory (https://github.com/briantist/galactory/pull/29).
- upstream proxying - proxied requests used the ``Accept:`` header of the request, sometimes resulting in HTML from the upstream and a resulting 500 error since the response was not JSON (https://github.com/briantist/galactory/issues/31).
- upstream proxying - proxied requests with an ``Accept-Encoding: br`` (brotli compression) header would fail decoding because of the lack of a brotli decoder (https://github.com/briantist/galactory/pull/32).

v0.7.0
======

Release Summary
---------------

Property setting is now done at upload time, which removes another piece of Pro license code, but may cause issues with certain reverse proxy configurations. A new fallback option is introduced to use the old behavior, but it may be removed in a future version.

Breaking Changes / Porting Guide
--------------------------------

- property setting - by default properties are now set on the initial upload of a collection to Artifactory. This removes an additional roundtrip to the server, and removes another API call that requires a Pro license of Artifactory. However, some reverse proxy configurations will not work with this. A new parameter ``USE_PROPERTY_FALLBACK`` has been added which will use the old behavior of setting properties in a second request,  but this will still require a Pro license to use. This option may be removed in a future version. See (https://github.com/briantist/galactory/issues/19).

v0.6.0
======

Release Summary
---------------

With this release we've added the ability to block the use of a configured API key with the publish endpoint, preventing clients from publishing anonymously.

Minor Changes
-------------

- manifest loading - galactory no longer uses Artifactory's "Archive Entry Download" endpoint, removing one piece of code that requires a pro license or greater (https://github.com/briantist/galactory/issues/5, https://github.com/briantist/galactory/pull/16).
- publish endpoint - add ``PUBLISH_SKIP_CONFIGURED_KEY`` option which disallows using a configured API key on the ``publish`` endpoint (https://github.com/briantist/galactory/issues/14).

v0.5.0
======

Release Summary
---------------

This release contains cache control options. This enables more scenarios for proxying, such as proxying with no Artifactory API key, or one without write permission. The cache expiry time can now be configured, and it can be set independently in different galactory instances pointed at the same cache in artifactory.

Minor Changes
-------------

- proxy cache - finer control over when and what gets cached when proxying upstream, allowing for proxy configurations with less permission in artifactory (https://github.com/briantist/galactory/issues/4, https://github.com/briantist/galactory/pull/13).

v0.4.0
======

Release Summary
---------------

This release adds much improved configuration support.

Minor Changes
-------------

- configuration - all options can now be configured via environment variables, direct in CLI, or in config files (https://github.com/briantist/galactory/pull/12).

v0.3.1
======

Release Summary
---------------

ARM64 containers are now part of the release process. The meaning of the ``latest`` tag for containers now refers to the build from the latest *git tag* rather than the latest commit.
Containers are now also tagged with the branch name to correspond to the latest commit in a specific branch, for example ``ghcr.io/briantist/galactory:main``.
There are no functional changes in this release.

Minor Changes
-------------

- container releases - change meaning of container tags, add ARM64 container releases (https://github.com/briantist/galactory/pull/10, https://github.com/briantist/galactory/pull/11).

v0.3.0
======

Release Summary
---------------

Some big reliability and performance enhancements included in ths release.

Minor Changes
-------------

- connections - retries are now done automatically both on proxied upstream requests and on requests to Artifactory (https://github.com/briantist/galactory/pull/7, https://github.com/briantist/galactory/pull/8).
- performance - optimizations when iterating collections allow a huge reduction in the number of requests to artifactory needed (https://github.com/briantist/galactory/pull/9).

v0.2.0
======

Release Summary
---------------

Adds a new option to control the server name in generated links.

Minor Changes
-------------

- Allow server name to be configurable via the ``--server-name`` CLI option (https://github.com/briantist/galactory/pull/3).

v0.1.0
======

Release Summary
---------------

The first release of Galactory, with support for upstream proxying.
