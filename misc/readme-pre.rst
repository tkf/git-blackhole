===========================================================================
 ``git-blackhole`` --- Continuous backup and recoverable trash can for Git
===========================================================================

|build-status|

.. |build-status|
   image:: https://travis-ci.org/tkf/git-blackhole.svg?branch=master
   :target: https://travis-ci.org/tkf/git-blackhole
   :alt: Build Status

Synopsis
========

| git blackhole init [--name <repo>] <url>
| git blackhole push [--remote <repo>]
| git blackhole trash-branch [--remote <repo>] <branch>
| git blackhole trash-stash [--remote <repo>] <stash_range>
| git blackhole [<subcommand>] (-h|--help)
