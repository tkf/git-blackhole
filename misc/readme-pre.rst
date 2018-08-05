===========================================================================
 ``git-blackhole`` --- Continuous backup and recoverable trash can for Git
===========================================================================

|logo|

    Logo by `@reallinfo <https://github.com/reallinfo>`_.  The logo is
    licensed under a `Creative Commons Attribution 4.0 International
    License <https://creativecommons.org/licenses/by/4.0/>`_.

|pypi| |build-status| |coveralls|

Installation
============

Use pip::

  pip install git-blackhole

Directly download from GitHub::

  curl https://raw.githubusercontent.com/tkf/git-blackhole/master/git_blackhole.py --output git-blackhole
  chmod u+x git-blackhole


Synopsis
========

.. code:: shell

  git blackhole init [--name <repo>] <url>
  git blackhole push [--remote <repo>]
  git blackhole warp [--remote <repo>]
  git blackhole trash-branch [--remote <repo>] <branch>
  git blackhole trash-stash [--remote <repo>] <stash_range>
  git blackhole fetch-trash [--remote <repo>]
  git blackhole ls-trash
  git blackhole show-trash
  git blackhole rm-local-trash (--all | <ref>...)
  git blackhole [<subcommand>] (-h|--help)
