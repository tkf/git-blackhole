=====================
 Test ``--ref-glob``
=====================

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


Specific preparation
====================
::

  $ git blackhole init ../blackhole.git
  $ git blackhole push
  To ../blackhole.git
   * [new branch]      master -> heads/*/local/master (glob)
   * [new branch]      HEAD -> heads/*/local/HEAD (glob)

Test with ``refs/wip``
=====================
::

  $ git update-ref refs/wip/master master
  $ git blackhole push
  Everything up-to-date
  $ git blackhole push --ref-glob "refs/wip/*"
  To ../blackhole.git
   * [new branch]      refs/wip/master -> refs/wip/*/local/master (glob)
  $ git ls-remote blackhole 'refs/wip/*' \
  >   | sed -r "s#.{40}\trefs/wip/$(hostname)/##g"
  local/master
