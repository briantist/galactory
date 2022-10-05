=======================
galactory Release Notes
=======================

.. contents:: Topics


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
