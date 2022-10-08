=======================
galactory Release Notes
=======================

.. contents:: Topics


v0.6.0
======

Release Summary
---------------

With this release we've hopefully gotten rid of the last code that requires a paid Artifactory license, so galactory should now be fully usable with Artifactory OSS. We've also added the ability to block the use of a configured API key with the publish endpoint, preventing clients from publishing anonymously.

Minor Changes
-------------

- manifest loading - galactory no longer uses Artifactory's "Archive Entry Download" endpoint, removing the need to use a pro license or greater (https://github.com/briantist/galactory/issues/5, https://github.com/briantist/galactory/pull/16).
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
