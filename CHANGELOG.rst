=======================
galactory Release Notes
=======================

.. contents:: Topics


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
