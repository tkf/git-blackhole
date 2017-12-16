.. -*- mode: rst -*-

===================================================
 Tests for ``--verbose`` and ``--dry-run`` options
===================================================

.. [[[cog import cog; cog.outl(open('preamble.rest').read())]]]

Some preparation needed for cram test::

  $ export HOME=$PWD
  $ git config --global user.email "test@blackhole"
  $ git config --global user.name "Test Black-Hole"

  $ git init --quiet --bare blackhole.git
  $ git init --quiet --bare origin.git
  $ git init --quiet local
  $ cd local/

Useful functions::

  $ commit(){
  >   change="${1:-change}"
  >   file="${3:-README.txt}"
  >   message="${2:-Append '$change' to $file}"
  >   echo "$change" >> "$file"
  >   git add "$file"
  >   git commit --quiet --message "$message" -- "$file"
  > }

  $ mkbranch(){
  >     branch="${1:-garbage}"
  >     shift
  >     git checkout --quiet -b "$branch"
  >     commit "$@"
  >     git checkout --quiet -
  > }

Add some changes in the local repository::

  $ commit
  $ git remote add origin ../origin.git
  $ git push --quiet --set-upstream origin master
  Branch master set up to track remote branch master from origin.

.. [[[end]]]


``git blackhole init --verbose --dry-run``
==========================================

::

  $ git blackhole init -vn ../blackhole.git | sed s/$(hostname)/myhost/g
  git remote add blackhole ../blackhole.git
  git config remote.blackhole.fetch +refs/heads/heads/myhost/local/*:refs/remotes/blackhole/*
  git config remote.blackhole.push +refs/heads/*:heads/myhost/local/*


Other commands require blackhole-initialized repository so let's run
it for real.::

  $ git blackhole init ../blackhole.git 2>/dev/null


``git blackhole push --verbose --dry-run``
==========================================
::

  $ git blackhole push -vn | sed s/$(hostname)/myhost/g
  git push --force blackhole master HEAD:refs/heads/heads/myhost/local/HEAD


``git blackhole trash-branch --verbose --dry-run``
==================================================

Make garbage branch::

  $ mkbranch
  $ git branch --list
    garbage
  * master

Run ``trash-branch``::

  $ git blackhole trash-branch -vn garbage
  git push ../blackhole.git *:refs/heads/trash/*/local/*/* (glob)
  git branch --delete --force garbage

It should not remove the branch::

  $ git branch --list
    garbage
  * master


``git blackhole trash-stash --verbose --dry-run``
=================================================

Make a stash::

  $ echo change >> README.txt
  $ git stash save --quiet
  $ git stash list
  stash@{0}: WIP on master: * (glob)

Run ``trash-stash``::

  $ git blackhole trash-stash -vn 0
  git push ../blackhole.git *:refs/heads/trash/*/local/*/* (glob)
  git stash drop stash@{0}

It should not remove the stash::

  $ git stash list
  stash@{0}: WIP on master: * (glob)
