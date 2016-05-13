==============
 Nit-pickings
==============

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
  >   file="${1:-README.txt}"
  >   change="${3:-change}"
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


``git blackhole init``
======================

Running ``git blackhole init`` at non-root should work.::

  $ mkdir sub
  $ commit sub/test.txt
  $ cd sub
  $ git blackhole init ../blackhole.git
  $ cd ..
  $ tail -n4 .git/config | sed s/$(hostname)/myhost/g
  [remote "blackhole"]
  	url = ../blackhole.git
  	fetch = +refs/heads/heads/myhost/local/*:refs/remotes/blackhole/*
  	push = +refs/heads/*:heads/myhost/local/*

``git blackhole push``
======================

``git blackhole push`` can take ``--no-verify``::

  $ ln -s /bin/false .git/hooks/pre-push
  $ git push --quiet origin master
  error: failed to push some refs to '../origin.git'
  [1]
  $ git blackhole push
  error: failed to push some refs to '../blackhole.git'
  [1]
  $ git blackhole push --no-verify
  To ../blackhole.git
   * [new branch]      master -> heads/*/local/master (glob)
   * [new branch]      HEAD -> heads/*/local/HEAD (glob)
  $ rm .git/hooks/pre-push


``git blackhole trash-branch``
==============================

Running ``git blackhole trash-branch`` at non-root should work.::

  $ mkbranch
  $ cd sub
  $ git blackhole trash-branch garbage
  To ../blackhole.git
   * [new branch]      * -> trash/*/local/*/* (glob)
  Deleted branch garbage (was *). (glob)
  $ cd ..

List remote branch names::

  $ git ls-remote blackhole 'refs/heads/trash/*' \
  >   | sed -r "s#.{40}\trefs/heads/trash/$(hostname)/##g"
  local/../.{38} (re)

Make sure that ``/sub/`` is not included in remote branch name::

  $ git ls-remote blackhole 'refs/heads/trash/*' | grep /local/sub/
  [1]

``git blackhole trash-branch`` can take ``--no-verify``::

  $ ln -s /bin/false .git/hooks/pre-push
  $ mkbranch garbage another-file.txt
  $ git blackhole trash-branch garbage
  error: failed to push some refs to '../blackhole.git'
  [123]
  $ git blackhole trash-branch --no-verify garbage
  To ../blackhole.git
   * [new branch]      * -> trash/*/local/*/* (glob)
  Deleted branch garbage (was *). (glob)
  $ rm .git/hooks/pre-push


``git blackhole trash-stash``
=============================

Running ``git blackhole trash-stash`` at non-root should work.::

  $ echo change 0 >> README.txt
  $ git stash
  Saved working directory and index state WIP on master: * (glob)
  HEAD is now at * (glob)
  $ git stash list
  stash@{0}: WIP on master: * (glob)
  $ cd sub
  $ git blackhole trash-stash 0
  To ../blackhole.git
   * [new branch]      * -> trash/*/local/*/* (glob)
  Dropped stash@{0} (*) (glob)
  $ cd ..

List remote branch names::

  $ git ls-remote blackhole 'refs/heads/trash/*' \
  >   | sed -r "s#.{40}\trefs/heads/trash/$(hostname)/##g"
  local/../.{38} (re)
  local/../.{38} (re)
  local/../.{38} (re)

Make sure that ``/sub/`` is not included in remote branch name::

  $ git ls-remote blackhole 'refs/heads/trash/*' | grep /local/sub/
  [1]

``git blackhole trash-stash`` can take ``--no-verify``::

  $ ln -s /bin/false .git/hooks/pre-push
  $ echo change >> README.txt
  $ git stash
  Saved working directory and index state WIP on master: * (glob)
  HEAD is now at * (glob)
  $ git blackhole trash-stash 0
  error: failed to push some refs to '../blackhole.git'
  [123]
  $ git blackhole trash-stash --no-verify 0
  To ../blackhole.git
   * [new branch]      * -> trash/*/local/*/* (glob)
  Dropped stash@{0} (*) (glob)
  $ rm .git/hooks/pre-push
