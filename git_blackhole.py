"""
Connecting your repository to the blackhole which can swallow everything.

The aim of ``git-blackhole`` is to connect any of your repositories to
a single repository ("blackhole" repository) to which you can push any
commits --- WIP commits, branches no longer needed, and useless
stashes.

There are three main features of ``git-blackhole``:

1. **Continuous backup**.  You can use ``git-blackhole`` to
   continuously backup commits in background to a remote repository
   (or actually any repository) called blackhole repository.

   Run ``git blackhole init`` and then setup ``post-commit`` hook to
   run ``git blackhole push``.  See the help of ``git blackhole push``
   for the details.

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

"""

from __future__ import print_function

import os
import sys
from subprocess import check_output, CalledProcessError

__version__ = '0.0.0'
__author__ = 'Takafumi Arakaki'
__license__ = None


def make_run(verbose, dry_run, check=True):
    from subprocess import check_call, call

    def run(*command, **kwds):
        out = kwds.pop('out', False)
        if verbose:
            redirects = ()
            if 'stdout' in kwds:
                redirects = ('>', kwds['stdout'].name)
            print(' '.join(command + redirects))
            sys.stdout.flush()
        if out:
            return check_output(command, **kwds)
        elif not dry_run:
            return (check_call if check else call)(command, **kwds)
    return run


def getprefix(type, info=None):
    info = info or getrecinfo()
    return '{type}/{host}/{relpath}'.format(
        type=type,
        **info)


def getrecinfo():
    from socket import gethostname
    repo = check_output(['git', 'rev-parse', '--show-toplevel'])
    repo = repo.decode().rstrip()
    return dict(
        host=gethostname(),
        repo=repo,
        relpath=os.path.relpath(repo, os.path.expanduser('~')),
        git_blackhole=__version__)


def getbranches():
    checkout = None
    branches = []
    out = check_output(['git', 'branch', '--list']).decode()
    for line in out.splitlines():
        br = line.lstrip('*').strip()
        branches.append(br)
        if line.startswith('*'):
            checkout = br
    return branches, checkout


def getrefs():
    out = check_output(['git', 'show-ref']).decode()
    for line in out.splitlines():
        yield line.rstrip().split(None, 1)


def getrefnames():
    return [ref for (_sha1, ref) in getrefs()]


def getconfig(name, aslist=False):
    try:
        out = check_output(['git', 'config', '--null'] + (
            ['--get-all'] if aslist else ['--get']
        ) + [name]).decode()
    except CalledProcessError as err:
        if err.returncode == 1:
            return None
        else:
            raise
    return out.split('\0')[:-1] if aslist else out.rstrip('\0')


def check_communicate(cmd, input, **kwds):
    """
    Run ``Popen(cmd, **kwds).communicate(input)`` and bark on an error.

    >>> check_communicate(['cat'], 'hey') == b'hey'
    True

    """
    from subprocess import Popen, PIPE
    if 'stderr' not in kwds:
        kwds['stderr'] = PIPE
    proc = Popen(cmd, stdin=PIPE, stdout=PIPE, **kwds)
    if input is not None and not isinstance(input, bytes):
        input = input.encode()
    (stdout, stderr) = proc.communicate(input)
    if proc.returncode != 0:
        output = stdout if stderr is None else stderr
        raise CalledProcessError(proc.returncode, cmd, output)
    return stdout


def git_annot_commit(message, parent):
    """
    Make a commit with `message` on top of `parent` commit.

    This is "annotation commit" in a sense that it does not add change
    to `parent` version.  It just adds a commit with a message which
    can contain additional information (annotation) about `parent`
    commit.

    See:

    * https://git-scm.com/book/en/v2/Git-Internals-Git-Objects
    * man git-rev-parse
    * man git-commit-tree

    """
    tree = check_output(['git', 'rev-parse', '{0}^{{tree}}'.format(parent)])
    tree = tree.decode().rstrip('\n')
    rev = check_communicate(['git', 'commit-tree', tree, '-p', parent],
                            message)
    return rev.decode().rstrip('\n')


def git_json_commit(heading, obj, parent):
    import json
    return git_annot_commit(
        "GIT-BLACKHOLE: {}\n\nGIT-BLACKHOLE-JSON:\n{}"
        .format(heading, json.dumps(obj)),
        parent)


def parse_json_message(message):
    import json
    heading, _, cookie, rest = message.split('\n', 3)
    preh = 'GIT-BLACKHOLE: '
    assert heading.startswith(preh)
    assert cookie == 'GIT-BLACKHOLE-JSON:'
    return (heading[len(preh):], json.loads(rest))


def cmd_push(remote, force=False, verify=None):
    cmd = ['git', 'push']
    if force:
        cmd.append('--force')
    if verify is True:
        cmd.append('--verify')
    elif verify is False:
        cmd.append('--no-verify')
    cmd.append(remote)
    return cmd


def trash_commitish(commitish, remote, info, headingtemp,
                    verbose, dry_run, **kwds):
    """
    Push `commitish` to `remote` trash.
    """
    run = make_run(verbose, dry_run)
    prefix = getprefix('trash')
    rev = check_output(['git', 'rev-parse', commitish]).strip()
    url = getconfig('remote.{0}.url'.format(remote))
    info = dict(info, **getrecinfo())
    heading = headingtemp.format(**info)
    rev = git_json_commit(heading, info, commitish)
    refspec = '{0}:refs/heads/{1}/{2}/{3}'.format(rev, prefix,
                                                  rev[:2], rev[2:])
    run(*cmd_push(url, **kwds) + [refspec])
    return refspec


def trashinfo(rev):
    out = check_output(['git', 'show', '--format=format:%B', rev])
    heading, obj = parse_json_message(out.decode())
    rev0 = check_output(['git', 'rev-parse', rev + '^'])
    return dict(obj, heading=heading, rev_info=rev, rev=rev0.decode().strip())


def gettrashes():
    out = check_output(['git', 'rev-parse', '--glob=refs/bh/trash/*'])
    revs = out.decode().splitlines()
    return list(map(trashinfo, revs))


def show_trashes(trashes, verbose):
    for trash in trashes:
        print(trash['rev'])
        if verbose:
            keys = set(trash) - {'heading', 'rev', 'git_blackhole'}
            for k in keys:
                print('  ', k, ': ', trash[k], sep='')


def git_stash_list():
    output = check_output(
        ["git", "stash", "list", "--format=%gD %H"])
    # man git-log > PRETTY FORMATS
    return output.decode().splitlines()


def parse_stash(line):
    """
    Parse a line of `git_stash_list` output.

    >>> parse_stash('refs/stash@{0} 29453bf380ff2e3aabf932a08287a162bc12d218')
    (0, 'refs/stash@{0}', '29453bf380ff2e3aabf932a08287a162bc12d218')

    """
    (reflog_selector, commit_hash) = line.split()
    num = int(reflog_selector.lstrip('refs/stash@{').rstrip('}'))
    return (num, reflog_selector, commit_hash)


def parse_range(stash_range):
    """
    Parse stash range syntax

    >>> in_range = parse_range('0, 3-5, 8-')
    >>> for i in range(11):
    ...     print('{0} {1}'.format(i, in_range(i)))
    0 True
    1 False
    2 False
    3 True
    4 True
    5 True
    6 False
    7 False
    8 True
    9 True
    10 True

    """

    def minmax(raw):
        if '-' in raw:
            (low, high) = map(str.strip, raw.split('-'))
            return (int(low) if low else 0,
                    int(high) if high else None)
        else:
            return (int(raw), int(raw))

    def in_range(num):
        for (low, high) in ranges:
            if high is None and low <= num:
                return True
            elif low <= num <= high:
                return True
        return False

    if stash_range:
        ranges = list(map(minmax, stash_range.split(',')))
        return in_range
    else:
        return lambda _: True


def refspecs_for_stashes(num, info=None):
    """
    Compile refspecs for stashes and and return as a list strings.

    >>> refspecs_for_stashes(3, info=dict(
    ...     host='myhost',
    ...     relpath='local/repo',
    ... ))                                 # doctest: +NORMALIZE_WHITESPACE
    ['stash@{0}:refs/heads/stash/myhost/local/repo/0',
     'stash@{1}:refs/heads/stash/myhost/local/repo/1',
     'stash@{2}:refs/heads/stash/myhost/local/repo/2']

    """
    prefix = getprefix('stash', info=info)
    tmpl = r'stash@{{{0}}}:refs/heads/' + prefix + '/{0}'
    return list(map(tmpl.format, range(num)))


def refspecs_from_globs(globs, refs=None, info=None):
    """
    Compile refspecs for stashes and and return as a list strings.

    >>> refspecs_from_globs(
    ...     ['refs/wip/*'],
    ...     refs=[
    ...         'refs/heads/master',
    ...         'refs/remotes/wip/master',
    ...         'refs/wip/master',
    ...     ],
    ...     info=dict(
    ...         host='myhost',
    ...         relpath='local/repo',
    ... ))                                 # doctest: +NORMALIZE_WHITESPACE
    ['refs/wip/master:refs/wip/myhost/local/repo/master']

    """
    import fnmatch
    info = info or getrecinfo()
    allrefs = refs or getrefnames()
    refs = []
    for pattern in globs:
        refs.extend(fnmatch.filter(allrefs, pattern))
    refs = fnmatch.filter(refs, 'refs/*')
    refs = [r for r in refs if not r.startswith('refs/remotes/')]
    refspecs = []
    for r in refs:
        (_, type, rest) = r.split('/', 2)
        prefix = getprefix(type, info=info)
        refspecs.append('{0}:refs/{1}/{2}'.format(r, prefix, rest))
    return refspecs


def cli_init(name, url, verbose, dry_run, _prefix=None):
    """
    Add blackhole remote at `url` with `name`.

    This command runs ``git remote add <name> <url>`` and configure
    appropriate `remote.<name>.fetch` and `remote.<name>.pushe`
    properties so that remote blackhole repository at `url` acts
    as if it is a yet another remote repository.

    To be more precise, each local branch is related to the branch at
    the blackhole remote with the prefix ``heads/$HOST/$RELPATH/``
    where ``$HOST`` is the name of local machine and ``$RELPATH`` is
    the path of the repository relative to ``$HOME``.

    """
    run = make_run(verbose, dry_run)
    prefix = _prefix or getprefix('heads')
    if '/.' in prefix:
        print('git blackhole cannot be configured for repositories',
              'under a hidden directory (starting with ".")')
        return 1
    run('git', 'remote', 'add', name, url)
    run('git', 'config', 'remote.{0}.fetch'.format(name),
        '+refs/heads/{0}/*:refs/remotes/{1}/*' .format(prefix, name))
    run('git', 'config', 'remote.{0}.push'.format(name),
        '+refs/heads/*:{0}/*'.format(prefix))


def cli_warp(host, relpath, name, remote, url, **kwds):
    """
    Peek into other repositories through the blackhole.
    """
    if not (host or relpath):
        print('need HOST or --relpath=RELPATH')
        return 2
    if not url:
        url = getconfig('remote.{0}.url'.format(remote))
        if url is None:
            print('need --url in an uninitialized repository')
            return 1

    info = getrecinfo()
    info.update(
        host=host or info['host'],
        relpath=relpath or info['relpath'],
    )
    prefix = getprefix('heads', info)
    if not name:
        name = 'bh_' + host
    return cli_init(_prefix=prefix, name=name, url=url, **kwds)


def cli_push(verbose, dry_run, ref_globs, remote, skip_if_no_blackhole,
             **kwds):
    """
    Push branches and HEAD forcefully to blackhole `remote`.

    Note that local HEAD is pushed to the remote branch named
    ``heads/$HOST/$RELPATH/HEAD`` (see help of ``git blackhole init``)
    instead of real remote HEAD.  This way, if the blackhole remote is
    shared with other machine, you can recover the HEAD at ``$HOST``.

    It is useful to call this command from the ``post-commit`` hook::

      nohup git blackhole push --no-verify &> /dev/null &

    See also `githooks(5)`.

    To push revisions created by git-wip_ command, add option
    ``--ref-glob='refs/wip/*'``.

    .. _git-wip: https://github.com/bartman/git-wip

    """
    if getconfig('remote.{0}.url'.format(remote)) is None:
        if skip_if_no_blackhole:
            return
        else:
            print("git blackhole is not configured.")
            print("Run: git blackhole init URL")
            return 1
    run = make_run(verbose, dry_run, check=False)
    prefix = getprefix('heads')
    branches, _checkout = getbranches()

    # Build "git push" command options:
    cmd = cmd_push(remote=remote, force=True, **kwds)
    cmd.extend(branches)
    cmd.extend(refspecs_for_stashes(len(git_stash_list())))
    cmd.extend(refspecs_from_globs(ref_globs))
    # Explicitly specify destination (HEAD:HEAD didn't work):
    cmd.append('HEAD:refs/heads/{0}/HEAD'.format(prefix))

    return run(*cmd)


def cli_trash_branch(branches, verbose, dry_run, **kwds):
    """
    [EXPERIMENTAL] Save `branch` in blackhole `remote` before deletion.

    The `branch` is pushed to the branch of the blackhole `remote`
    named ``trash/$HOST/$RELPATH/$SHA1[:2]/$SHA1[2:]`` where ``$HOST``
    is the name of local machine, ``$RELPATH`` is the path of the
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

    """
    """
    - FIXME: Maybe I should remove ``$HOST/$RELPATH`` part and use
      branch named ``trash/$REV[:2]/$REV[2:]``, since the JSON has all
      the info I need.
    """
    run = make_run(verbose, dry_run)
    _branches, checkout = getbranches()
    final_code = None
    for branch in branches:
        code = trash_branch(run, checkout, branch,
                            verbose=verbose, dry_run=dry_run,
                            **kwds)
        if code:
            final_code = code
    return final_code


def trash_branch(run, checkout, branch, verbose, dry_run,
                 remote, remove_upstream,
                 **kwds):
    if branch == checkout:
        print("Cannot trash the branch '{0}' which you are currently on."
              .format(branch))
        return 1
    if remove_upstream:
        upstream_repo = getconfig('branch.{0}.remote'.format(branch))
        upstream_branch = getconfig('branch.{0}.merge'.format(branch))
    trash_commitish(
        branch, remote, dict(command='trash-branch', branch=branch),
        'Trash branch "{branch}" at {host}:{repo}',
        verbose, dry_run, **kwds)
    run('git', 'branch', '--delete', '--force', branch)

    if remove_upstream:
        if upstream_repo is None:
            print('Not removing upstream branch as upstream is'
                  ' not configured.')
        else:
            run('git', 'push', upstream_repo, ':' + upstream_branch)


def cli_trash_stash(remote, stash_range, keep_stashes,
                    verbose, dry_run, **kwds):
    """
    [EXPERIMENTAL] Save stashes in blackhole `remote` before deletion.

    It works as (almost) the same way as ``git blackhole trash-branch``.

    Several stashes can be specified in `stash_range`.  It takes
    single numbers (e.g., 3) and ranges (e.g., 3-5 or 8-) separated by
    commas.  Each range is in the form ``x-y`` which selects stashes
    ``x, x+1, x+2, ..., y``.  The upper limit ``y`` can be omitted,
    meaning "until the last stash".  For example, when you have
    stashes 0 to 10, ``git blackhole trash-stash 0,3-5,8-`` removes
    stashes 0, 3, 4, 5, 8, 9, and 10.

    """
    run = make_run(verbose, dry_run)
    in_range = parse_range(stash_range)
    stashes = [s for s in map(parse_stash, git_stash_list())
               if in_range(s[0])]

    if not stashes:
        print('No stash is found.')
        return

    # Using "git stash drop stash@{SHA1}" is unreliable because
    # sometime git confuses SHA1 with date (e.g., SHA1 could starts
    # with "1d").  So "stash@{N}" must be used.  However, "N" would
    # change if newer stashes are popped.  Hence `reversed`.
    for (num, raw, sha1) in reversed(stashes):
        if in_range(num):
            stash = 'stash@{{{0}}}'.format(num)
            trash_commitish(
                sha1, remote, dict(command='trash-stash'),
                'Trash a stash at {host}:{repo}',
                verbose, dry_run, **kwds)
            if not keep_stashes:
                run('git', 'stash', 'drop', stash)


def cli_fetch_trash(remote, verbose, dry_run):
    """
    Fetch trashes from remote to ``refs/bh/trash/``.
    """
    run = make_run(verbose, dry_run)
    info = dict(getrecinfo(), host='*')
    prefix = getprefix('trash', info)
    out = run('git', 'ls-remote', 'blackhole',
              'refs/heads/' + prefix + '/*', out=True)
    refs = [l.split(None, 1)[1] for l in out.decode().splitlines()]
    cmd = ['git', 'fetch']
    if verbose:
        cmd.append('--verbose')
    cmd.append(remote)
    cmd.append('--')
    cmd.extend(
        '{0}:refs/bh/trash/{1[0]}/{1[1]}'.format(r, r.rsplit('/', 2)[-2:])
        for r in refs
    )
    run(*cmd)


def cli_ls_trash(verbose, dry_run):
    """
    List trashes fetched by ``git blackhole fetch-trash``.
    """
    show_trashes(gettrashes(), verbose)


def cli_show_trash(verbose, dry_run):
    """
    Run ``git show`` on trashes fetched by ``git blackhole fetch-trash``.
    """
    revs = [t['rev'] for t in gettrashes()]
    run = make_run(verbose, dry_run)
    run('git', 'show', *revs)


def cli_rm_local_trash(verbose, dry_run, refs, all):
    """
    Remove trashes fetched by ``git blackhole fetch-trash``.
    """
    run = make_run(verbose, dry_run)
    if all:
        out = check_output(['git', 'rev-parse', '--symbolic',
                            '--glob=refs/bh/trash/*'])
        refs = out.decode().splitlines()
    for r in refs:
        run('git', 'update-ref', '-d', r)


def make_parser(doc=__doc__):
    import argparse

    class FormatterClass(argparse.RawDescriptionHelpFormatter,
                         argparse.ArgumentDefaultsHelpFormatter):
        pass

    parser = argparse.ArgumentParser(
        formatter_class=FormatterClass,
        description=doc)
    parser.add_argument('--debug', default=False, action='store_true')
    subparsers = parser.add_subparsers()

    def subp(command, func):
        doc = func.__doc__
        title = None
        for title in filter(None, map(str.strip, (doc or '').splitlines())):
            break
        p = subparsers.add_parser(
            command,
            formatter_class=FormatterClass,
            help=title,
            description=doc)
        p.set_defaults(func=func)
        p.add_argument(
            '--verbose', '-v', default=False, action='store_true',
            help='print git commands to run')
        p.add_argument(
            '--dry-run', '-n', default=False, action='store_true',
            help='do nothing when given. Use it with --verbose to see '
            'what is going to happen.')
        return p

    def push_common(p):
        p.add_argument('--verify', default=None, action='store_true',
                       help='passed to git-push')
        p.add_argument('--no-verify', dest='verify', action='store_false',
                       help='passed to git-push')

    p = subp('init', cli_init)
    p.add_argument('--name', default='blackhole',
                   help='name of the remote blackhole repository')
    p.add_argument('url',
                   help='URL of the remote blackhole repository')

    p = subp('warp', cli_warp)
    p.add_argument('--name', default='',
                   help='Name of the repository at <HOST>:<RELPATH>, '
                   ' accessed through the blackhole.'
                   ' Set to "bh_<HOST>" if empty.')
    p.add_argument('--url',
                   help='URL of the remote blackhole repository'
                   ' Use remote.<REMOTE>.url if not given.')
    p.add_argument('--remote', default='blackhole',
                   help='name of the remote blackhole repository')
    p.add_argument('--relpath',
                   help='The repository relative to the $HOME at <HOST>.'
                   ' Use current repository root if empty.')
    p.add_argument('host', default='', metavar='HOST', nargs='?',
                   help='The host name of the repository.'
                   ' Use current host name if empty.')

    p = subp('push', cli_push)
    push_common(p)
    p.add_argument('--remote', default='blackhole',
                   help='name of the remote blackhole repository')
    # FIXME: Stop hard-coding remote name.  Use git config system to
    # set default.
    p.add_argument('--ref-glob', action='append', default=[],
                   dest='ref_globs',
                   help='add glob patterns to be pushed, e.g., wip/*')
    p.add_argument('--ignore-error', action='store_true',
                   help='quick with code 0 on error')
    p.add_argument('--skip-if-no-blackhole', action='store_true',
                   help='do nothing if git blackhole is not configured')

    p = subp('trash-branch', cli_trash_branch)
    push_common(p)
    p.add_argument('branches', metavar='branch', nargs='+',
                   help='branch to be removed')
    p.add_argument('--remote', default='blackhole',  # FIXME: see above
                   help='name of the remote blackhole repository')
    p.add_argument('--remove-upstream', '-u', action='store_true',
                   help='remove branch in upstream repository.'
                   ' i.e., remove branch.<branch>.merge'
                   ' at branch.<branch>.remote. ignored if no remote'
                   ' is set.')

    p = subp('trash-stash', cli_trash_stash)
    push_common(p)
    p.add_argument('--remote', default='blackhole',  # FIXME: see above
                   help='name of the remote blackhole repository')
    p.add_argument(
        'stash_range',
        help='stashes to trash. It is comma-separated low-high range'
        ' (inclusive). e.g.: 0,3-5,8-')
    p.add_argument(
        '--keep-stashes', '-k', default=False, action='store_true',
        help='when this option is given, do not remove local stashes.')

    p = subp('fetch-trash', cli_fetch_trash)
    p.add_argument('--remote', default='blackhole',  # FIXME: see above
                   help='name of the remote blackhole repository')

    p = subp('ls-trash', cli_ls_trash)
    p = subp('show-trash', cli_show_trash)

    p = subp('rm-local-trash', cli_rm_local_trash)
    p.add_argument('--all', '-a', action='store_true',
                   help='remove all local copy of trashes')
    p.add_argument('refs', metavar='ref', nargs='*',
                   help='trash refs to be removed.')

    return parser


def main(args=None):
    parser = make_parser()
    ns = parser.parse_args(args)
    debug = ns.__dict__.pop('debug')
    ignore_error = ns.__dict__.pop('ignore_error', False)
    try:
        # FIXME: stop returning error code from cli_* functions
        code = (lambda func, **kwds: func(**kwds))(**vars(ns))
        if ignore_error:
            print("ignoring the error")
            return
        sys.exit(code)
    except CalledProcessError as err:
        if debug:
            raise
        if ignore_error:
            print("ignoring the error")
            return
        sys.exit(err.returncode + 122)


if __name__ == '__main__':
    main()
