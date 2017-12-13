===========================================================================
 ``git-blackhole`` --- Continuous backup and recoverable trash can for Git
===========================================================================

|build-status| |coveralls|

Installation
============

Use pip::

  pip install git-blackhole

Directly download from GitHub::

  curl https://raw.githubusercontent.com/tkf/git-blackhole/master/git_blackhole.py --output git-blackhole
  chmod u+x git-blackhole


Synopsis
========

| git blackhole init [--name <repo>] <url>
| git blackhole push [--remote <repo>]
| git blackhole trash-branch [--remote <repo>] <branch>
| git blackhole trash-stash [--remote <repo>] <stash_range>
| git blackhole [<subcommand>] (-h|--help)
