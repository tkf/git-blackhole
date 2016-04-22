=============
 Basic usage
=============

Preparation
===========

.. Some preparation needed for cram test:

  $ export HOME=$PWD
  $ git config --global user.email "test@blackhole"
  $ git config --global user.name "Test Black-Hole"

For a demonstration purpose, create a "remote" git repository used as
a blackehole::

  $ git init --bare blackhole.git
  Initialized empty Git repository in */blackhole.git/ (glob)

Initialize local git repository::

  $ git init local
  Initialized empty Git repository in */local/.git/ (glob)
  $ cd local/

First commit::

  $ touch README.txt
  $ git add .
  $ git commit --message 'First commit' > /dev/null


Initialize git-blackhole
========================

Initialize blackhole::

  $ git blackhole init ../blackhole.git

It just adds git remote named 'blackhole' (by default) and put prefix
``host/$HOST/$RELPATH`` to ``fetch`` and ``push`` configuration, where
``$RELPATH`` is the relative path to the repository from ``$HOME``::

  $ git remote
  blackhole
  $ tail -n4 .git/config | sed s/$(hostname)/myhost/g
  [remote "blackhole"]
  	url = ../blackhole.git
  	fetch = +refs/heads/host/myhost/local/*:refs/remotes/blackhole/*
  	push = +refs/heads/*:host/myhost/local/*


Push to the remote blackhole
============================

Since blackhole is just a remote repository, ``git push`` works
normally::

  $ git push blackhole master
  To ../blackhole.git
   * [new branch]      master -> host/*/local/master (glob)

There is ``git blackhole push`` command to push all local branches
*and* ``HEAD`` to the blackhole.  Note that local ``HEAD`` is pushed
to remote branch named ``host/$HOST/$RELPATH/HEAD``.::

  $ git blackhole push
  To ../blackhole.git
   * [new branch]      HEAD -> HEAD

Suppose you made a commit and pushed to the remote blackhole::

  $ echo change >> README.txt
  $ git add .
  $ git commit --message 'Second commit' > /dev/null
  $ git blackhole push
  To ../blackhole.git
     *  HEAD -> HEAD (glob)
     *  master -> host/*/local/master (glob)

but then decide to change the commit.::

  $ echo change >> README.txt
  $ git add .
  $ git commit --amend --message 'Changed second commit' > /dev/null

Running ``git blackhole push`` works just fine since internally it
uses ``git push --force``::

  $ git blackhole push
  To ../blackhole.git
   + * HEAD -> HEAD (forced update) (glob)
   + * master -> host/*/local/master (forced update) (glob)
