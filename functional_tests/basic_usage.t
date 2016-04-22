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

Initialize remote origin::

  $ git init --bare origin.git
  Initialized empty Git repository in */origin.git/ (glob)

Initialize local git repository::

  $ git init local
  Initialized empty Git repository in */local/.git/ (glob)
  $ cd local/

First commit::

  $ touch README.txt
  $ git add .
  $ git commit --message 'First commit' > /dev/null

Push it to the origin::

  $ git remote add origin ../origin.git
  $ git push --set-upstream origin master
  To ../origin.git
   * [new branch]      master -> master
  Branch master set up to track remote branch master from origin.


Initialize git-blackhole
========================

Initialize blackhole::

  $ git blackhole init ../blackhole.git

It just adds git remote named 'blackhole' (by default) and put prefix
``host/$HOST/$RELPATH`` to ``fetch`` and ``push`` configuration, where
``$RELPATH`` is the relative path to the repository from ``$HOME``::

  $ git remote
  blackhole
  origin
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
   * [new branch]      HEAD -> host/*/local/HEAD (glob)

Suppose you made a commit and pushed to the remote blackhole::

  $ echo change >> README.txt
  $ git add .
  $ git commit --message 'Second commit' > /dev/null
  $ git blackhole push
  To ../blackhole.git
     *  HEAD -> host/*/local/HEAD (glob)
     *  master -> host/*/local/master (glob)

but then decide to change the commit.::

  $ echo change >> README.txt
  $ git add .
  $ git commit --amend --message 'Changed second commit' > /dev/null

Running ``git blackhole push`` works just fine since internally it
uses ``git push --force``::

  $ git blackhole push
  To ../blackhole.git
   + * HEAD -> host/*/local/HEAD (forced update) (glob)
   + * master -> host/*/local/master (forced update) (glob)

(BTW, let's not forget to push to the normal repository origin)::

  $ git push origin
  To ../origin.git
     *  master -> master (glob)


Trash branch
============

Make a new branch which would be trashed later.::

  $ git checkout -b garbage
  Switched to a new branch 'garbage'
  $ echo change >> README.txt
  $ git add .
  $ git commit --message 'Garbage commit' > /dev/null
  $ git checkout master
  Switched to branch 'master'
  Your branch is up-to-date with 'origin/master'.
  $ git branch --list
    garbage
  * master

Trash ``garbage`` branch::

  $ git blackhole trash-branch garbage
  To ../blackhole.git
   * [new branch]      * -> trash/*/local/*/* (glob)
  Deleted branch garbage (was *). (glob)

Trashed branch is pushed to remote branch named
``trash/$HOST/$RELPATH/$REV[:2]/$REV[2:]``::

  $ git --git-dir=../blackhole.git branch --list | sed s/$(hostname)/myhost/g
    host/myhost/local/HEAD
    host/myhost/local/master
    trash/myhost/local/*/* (glob)
  $ b=$(git --git-dir=../blackhole.git branch --list | grep trash/)
  $ git --git-dir=../blackhole.git show $b
  commit * (glob)
  Author: Test Black-Hole <test@blackhole>
  Date:   * (glob)
  
      GIT-BLACKHOLE: Trash branch "garbage" at * (glob)
      
      {*"branch": "garbage"*} (glob)

In the commit message, the heading prefix "GIT-BLACKHOLE:" indicates
that this commit is made by git-blackhole.  The rest of the heading
has some human-readable message.  The second line is empty.  The third
line is JSON hodling some meta-info.

Note that you cannot trash current checked out branch::

  $ git checkout -b garbage
  Switched to a new branch 'garbage'
  $ git blackhole trash-branch garbage
  Cannot trash the branch 'garbage' which you are currently on.
  [1]

Suppose the branch to be trashed has upstream repository::

  $ git push --set-upstream origin garbage
  To ../origin.git
   * [new branch]      garbage -> garbage
  Branch garbage set up to track remote branch garbage from origin.
  $ git --git-dir=../origin.git branch --list
    garbage
  * master

Then, to remove upstream branch, pass ``--remove-upstream`` or ``-u``
option::

  $ git checkout master
  Switched to branch 'master'
  Your branch is up-to-date with 'origin/master'.
  $ git blackhole trash-branch --remove-upstream garbage
  To ../blackhole.git
   * [new branch]      * -> trash/*/local/*/* (glob)
  Deleted branch garbage (was *). (glob)
  To ../origin.git
   - [deleted]         garbage
  $ git --git-dir=../origin.git branch --list
  * master

Note that ``--remove-upstream`` is no-op when upstream repository is
not set.  To show this, let's make garbage branch once again.::

  $ git checkout -b garbage
  Switched to a new branch 'garbage'
  $ echo change >> README.txt
  $ git add .
  $ git commit --message 'Garbage commit' > /dev/null
  $ git checkout master
  Switched to branch 'master'
  Your branch is up-to-date with 'origin/master'.

The last line of the output of ``trash-branch --remove-upstream``
notify you that any upstream branch is not touched::

  $ git blackhole trash-branch --remove-upstream garbage
  To ../blackhole.git
   * [new branch]      * -> trash/*/local/*/* (glob)
  Deleted branch garbage (was *). (glob)
  Not removing upstream branch as upstream is not configured.
