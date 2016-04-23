=========================================================
 ``git-blackhole`` --- where you can throw everything to
=========================================================

Synopsis
========

| git blackhole init [--name <repo>] <url>
| git blackhole push [--remote <repo>]
| git blackhole trash-branch [--remote <repo>] <branch>
| git blackhole trash-stash [--remote <repo>] <stash_range>
| git blackhole [<subcommand>] (-h|--help)

Description
===========

The aim of ``git-blackhole`` is to connect any of your repositories to
a single repository to which you can throw everything --- WIP commits,
branches no longer needed, and useless stashes.

``git blackhole init``
    Add blackhole remote at `url` with `name`.

    This command runs ``git remote add <name> <url>`` and configure
    appropriate `remote.<name>.fetch` and `remote.<name>.pushe`
    properties so that remote blackhole repository at `url` acts
    as if it is a yet another remote repository.

    To be more precise, each local branch is related to the branch at
    the blackhole remote with the prefix ``host/$HOST/$RELPATH/``
    where ``$HOST`` is the name of local machine and ``$RELPATH`` is
    the path of the repository relative to ``$HOME``.




``git blackhole push``
    Push branches and HEAD forcefully to blackhole `remote`.

    Note that local HEAD is pushed to the remote branch named
    ``host/$HOST/$RELPATH/HEAD`` (see help of ``git blackhole init``)
    instead of real remote HEAD.  This way, if the blackhole remote is
    shared with other machine, you can recover the HEAD at ``$HOST``.

    It is useful to call this command from the ``post-commit`` hook::

      nohup git blackhole push --no-verify &> /dev/null &




``git blackhole trash-branch``
    [EXPERIMENTAL] Save `branch` in blackhole `remote` before deletion.

    The `branch` is pushed to the branch of the blackhole `remote`
    named ``trash/$HOST/$RELPATH/$SHA1[:2]/$SHA1[2:]`` where ``$HOST``
    is the name of local machine, ``$RELPATH`` is the path of the
    repository relative to ``$HOME``, and ``$SHA1`` is the revision of
    the commit.  (To be more precise, ``$SHA`` is the revision of the
    commit recording the revision of `branch` and some meta
    information).

    .. WARNING:: Currently, there is no commands to help retrieving
       trashed branches.  You have to do it manually using standard
       git commands.




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




Options
=======

``git blackhole init``
------------------------------

--verbose, -v  print git commands to run (default: False)

--dry-run, -n  do nothing when given. Use it with --verbose to see what is
               going to happen. (default: False)

--name NAME    name of the remote blackhole repository (default: blackhole)


``git blackhole push``
------------------------------

--verbose, -v    print git commands to run (default: False)

--dry-run, -n    do nothing when given. Use it with --verbose to see what is
                 going to happen. (default: False)

--verify         passed to git-push (default: None)

--no-verify      passed to git-push (default: True)

--remote REMOTE  name of the remote blackhole repository (default:
                 blackhole)


``git blackhole trash-branch``
------------------------------

--verbose, -v         print git commands to run (default: False)

--dry-run, -n         do nothing when given. Use it with --verbose to see
                      what is going to happen. (default: False)

--remote REMOTE       name of the remote blackhole repository (default:
                      blackhole)

--remove-upstream, -u
                      remove branch in upstream repository. (default: False)


``git blackhole trash-stash``
------------------------------

--verbose, -v       print git commands to run (default: False)

--dry-run, -n       do nothing when given. Use it with --verbose to see what
                    is going to happen. (default: False)

--remote REMOTE     name of the remote blackhole repository (default:
                    blackhole)

--keep-stashes, -k  when this option is given, do not remove local stashes.
                    (default: False)


See also
========

git-blackhole-basic-usage(5)
