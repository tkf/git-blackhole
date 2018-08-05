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

Description
===========

The aim of ``git-blackhole`` is to connect any of your repositories to
a single repository ("blackhole" repository) to which you can push any
commits --- WIP commits, branches no longer needed, and useless
stashes.

There are three main features of ``git-blackhole``:

1. **Continuous backup**.  You can use ``git-blackhole`` to
   continuously backup commits in background to a remote repository
   (or actually any repository) called *blackhole repository*.

   Run ``git blackhole init <url>`` and then setup ``post-commit``
   hook to run ``git blackhole push``.  See the help of ``git
   blackhole init`` and ``git blackhole push`` for the details.

   Note that blackhole repository at ``<url>`` can be used for
   arbitrary number of local repositories.  You just need to setup a
   single repository once.

   By combining with git-wip_ command, you can backup/share
   uncommitted changes as well.

2. **Sharing local repository state**.  Since ``git-blackhole`` can
   push commits and the location of HEAD to the blackhole repository,
   the state of a repository in one machine is accessible from other
   machines.

   For example, if you forget to push a commit from your desktop (to
   the usual remote) but want to resume the work from your laptop,
   ``git blackhole warp`` would be helpful.

3. **Recoverable trash can**.  Use ``git blackhole trash-branch`` and
   ``git blackhole trash-stashes`` to remove branches and stashes from
   the local repository after sending them to the remote blackhole
   repository.  They are stored remotely as ordinary branches so that
   you can recover them easily.

.. _git-wip: https://github.com/bartman/git-wip

``git blackhole init``
    Add blackhole remote at `url` with `name`.

    This command runs ``git remote add <name> <url>`` and configure
    appropriate `remote.<name>.fetch` and `remote.<name>.pushe`
    properties so that remote blackhole repository at `url` acts
    as if it is a yet another remote repository.

    To be more precise, each local branch is related to the branch at
    the blackhole remote with the prefix ``heads/$HOST/$REPOKEY/``
    where ``$HOST`` is the name of local machine and ``$REPOKEY`` is
    the path of the repository relative to ``$HOME``.




``git blackhole warp``
    Peek into other repositories through the blackhole.



``git blackhole push``
    Push branches and HEAD forcefully to blackhole `remote`.

    Note that local HEAD is pushed to the remote branch named
    ``heads/$HOST/$REPOKEY/HEAD`` (see help of ``git blackhole init``)
    instead of real remote HEAD.  This way, if the blackhole remote is
    shared with other machine, you can recover the HEAD at ``$HOST``.

    It is useful to call this command from the ``post-commit`` hook::

      nohup git blackhole push --no-verify &> /dev/null &

    See also `githooks(5)`.

    To push revisions created by git-wip_ command, add option
    ``--ref-glob='refs/wip/*'``.




``git blackhole trash-branch``
    [EXPERIMENTAL] Save `branch` in blackhole `remote` before deletion.

    The `branch` is pushed to the branch of the blackhole `remote`
    named ``trash/$HOST/$REPOKEY/$SHA1[:2]/$SHA1[2:]`` where ``$HOST``
    is the name of local machine, ``$REPOKEY`` is the path of the
    repository relative to ``$HOME``, and ``$SHA1`` is the revision of
    the commit.  (To be more precise, ``$SHA`` is the revision of the
    commit recording the revision of `branch` and some meta
    information).

    Use ``git blackhole fetch-trash`` to retrieve all trashes from
    remote and store them locally.  Commands ``git blackhole
    ls-branch`` and ``git blackhole show-branch`` can be used to list
    and show trash commits.

    .. WARNING:: Commands to navigate through trashes (e.g., ``git
       blackhole show-branch``) are still preliminary.  Furthermore,
       how trash metadata is stored may change in the future.
       However, since trashes are ordinary git branches in remote,
       they can be dealt with standard git commands.




``git blackhole trash-stash``
    [EXPERIMENTAL] Save stashes in blackhole `remote` before deletion.

    It works as (almost) the same way as ``git blackhole trash-branch``.

    Several stashes can be specified in `stash_range`.  It takes
    single numbers (e.g., 3) and ranges (e.g., 3-5 or 8-) separated by
    commas.  Each range is in the form ``x-y`` which selects stashes
    ``x, x+1, x+2, ..., y``.  The upper limit ``y`` can be omitted,
    meaning "until the last stash".  For example, when you have
    stashes 0 to 10, ``git blackhole trash-stash 0,3-5,8-`` removes
    stashes 0, 3, 4, 5, 8, 9, and 10.




``git blackhole fetch-trash``
    Fetch trashes from remote to ``refs/bh/trash/``.



``git blackhole ls-trash``
    List trashes fetched by ``git blackhole fetch-trash``.



``git blackhole show-trash``
    Run ``git show`` on trashes fetched by ``git blackhole fetch-trash``.



``git blackhole rm-local-trash``
    Remove trashes fetched by ``git blackhole fetch-trash``.



Options
=======

``git blackhole init``
------------------------------------------------------------------

--verbose, -v         print git commands to run (default: False)

--dry-run, -n         do nothing when given. Use it with --verbose to see
                      what is going to happen. (default: False)

--name NAME           name of the remote blackhole repository (default:
                      blackhole)

--mangle [{never,always,auto}]
                      Replace a dot right after the path separator (hidden
                      directories) to underscore "_" and use it as REPOKEY.
                      --mangle[=auto] means to do it only when necessary.
                      --mangle=always means to always set REPOKEY.
                      --mangle=never means no replacement and fail with an
                      error for hidden directories. (default: never)

--repokey REPOKEY     Set arbitrary REPOKEY for the location of this
                      repository in the blackhole repository. (default:
                      None)


``git blackhole warp``
------------------------------------------------------------------

--verbose, -v      print git commands to run (default: False)

--dry-run, -n      do nothing when given. Use it with --verbose to see what
                   is going to happen. (default: False)

--name NAME        Name of the repository at <HOST>:<REPOKEY>, accessed
                   through the blackhole. Set to "bh_<HOST>" if empty.
                   (default: )

--url URL          URL of the remote blackhole repository Use
                   remote.<REMOTE>.url if not given. (default: None)

--remote REMOTE    name of the remote blackhole repository (default:
                   blackhole)

--repokey REPOKEY  The repository relative to the $HOME at <HOST>. Use
                   current repository root if empty. (default: None)


``git blackhole push``
------------------------------------------------------------------

--verbose, -v         print git commands to run (default: False)

--dry-run, -n         do nothing when given. Use it with --verbose to see
                      what is going to happen. (default: False)

--verify              passed to git-push (default: None)

--no-verify           passed to git-push (default: True)

--remote REMOTE       name of the remote blackhole repository (default:
                      blackhole)

--ref-glob REF_GLOBS  add glob patterns to be pushed, e.g., wip/* (default:
                      [])

--ignore-error        quick with code 0 on error (default: False)

--skip-if-no-blackhole
                      do nothing if git blackhole is not configured
                      (default: False)


``git blackhole trash-branch``
------------------------------------------------------------------

--verbose, -v         print git commands to run (default: False)

--dry-run, -n         do nothing when given. Use it with --verbose to see
                      what is going to happen. (default: False)

--verify              passed to git-push (default: None)

--no-verify           passed to git-push (default: True)

--remote REMOTE       name of the remote blackhole repository (default:
                      blackhole)

--remove-upstream, -u
                      remove branch in upstream repository. i.e., remove
                      branch.<branch>.merge at branch.<branch>.remote.
                      ignored if no remote is set. (default: False)


``git blackhole trash-stash``
------------------------------------------------------------------

--verbose, -v       print git commands to run (default: False)

--dry-run, -n       do nothing when given. Use it with --verbose to see what
                    is going to happen. (default: False)

--verify            passed to git-push (default: None)

--no-verify         passed to git-push (default: True)

--remote REMOTE     name of the remote blackhole repository (default:
                    blackhole)

--keep-stashes, -k  when this option is given, do not remove local stashes.
                    (default: False)


``git blackhole fetch-trash``
------------------------------------------------------------------

--verbose, -v    print git commands to run (default: False)

--dry-run, -n    do nothing when given. Use it with --verbose to see what is
                 going to happen. (default: False)

--remote REMOTE  name of the remote blackhole repository (default:
                 blackhole)


``git blackhole ls-trash``
------------------------------------------------------------------

--verbose, -v  print git commands to run (default: False)

--dry-run, -n  do nothing when given. Use it with --verbose to see what is
               going to happen. (default: False)


``git blackhole show-trash``
------------------------------------------------------------------

--verbose, -v  print git commands to run (default: False)

--dry-run, -n  do nothing when given. Use it with --verbose to see what is
               going to happen. (default: False)


``git blackhole rm-local-trash``
------------------------------------------------------------------

--verbose, -v  print git commands to run (default: False)

--dry-run, -n  do nothing when given. Use it with --verbose to see what is
               going to happen. (default: False)

--all, -a      remove all local copy of trashes (default: False)


.. |logo|
   image:: logo/horizontal.png
   :align: middle
   :target: logo/
   :alt: Logo by @reallinfo https://github.com/reallinfo. This work is licensed under a Creative Commons Attribution 4.0 International License. (https://creativecommons.org/licenses/by/4.0/)

.. |pypi|
   image:: https://badge.fury.io/py/git-blackhole.svg
   :target: https://badge.fury.io/py/git-blackhole
   :alt: Python Package Index

.. |build-status|
   image:: https://travis-ci.org/tkf/git-blackhole.svg?branch=master
   :target: https://travis-ci.org/tkf/git-blackhole
   :alt: Build Status

.. |coveralls|
   image:: https://coveralls.io/repos/github/tkf/git-blackhole/badge.svg?branch=master
   :target: https://coveralls.io/github/tkf/git-blackhole?branch=master
   :alt: Test Coverage
