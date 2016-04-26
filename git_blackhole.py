"""
Connecting your repository to the blackhole which can swallow everything.

The aim of ``git-blackhole`` is to connect any of your repositories to
a single repository to which you can throw everything --- WIP commits,
branches no longer needed, and useless stashes.

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
        if verbose:
            redirects = ()
            if 'stdout' in kwds:
                redirects = ('>', kwds['stdout'].name)
            print(' '.join(command + redirects))
            sys.stdout.flush()
        if not dry_run:
            return (check_call if check else call)(command, **kwds)
    return run


def getprefix(type, info=None):
    info = info or getrecinfo()
    return '{type}/{host}/{relpath}'.format(
        relpath=os.path.relpath(info['repo'], os.path.expanduser('~')),
        type=type,
        **info)


def getrecinfo():
    from socket import gethostname
    repo = check_output(['git', 'rev-parse', '--show-toplevel'])
    return dict(
        host=gethostname(),
        repo=repo.decode().rstrip(),
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


def trash_commitish(commitish, remote, info, headingtemp,
                    verbose, dry_run):
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
    run('git', 'push', url, refspec)
    return refspec


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
    ...     repo=os.path.join(os.path.expanduser('~'), 'local/repo'),
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
    ...         repo=os.path.join(os.path.expanduser('~'), 'local/repo'),
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


def cli_init(name, url, verbose, dry_run):
    """
    Add blackhole remote at `url` with `name`.

    This command runs ``git remote add <name> <url>`` and configure
    appropriate `remote.<name>.fetch` and `remote.<name>.pushe`
    properties so that remote blackhole repository at `url` acts
    as if it is a yet another remote repository.

    To be more precise, each local branch is related to the branch at
    the blackhole remote with the prefix ``host/$HOST/$RELPATH/``
    where ``$HOST`` is the name of local machine and ``$RELPATH`` is
    the path of the repository relative to ``$HOME``.

    """
    run = make_run(verbose, dry_run)
    prefix = getprefix('host')
    run('git', 'remote', 'add', name, url)
    run('git', 'config', 'remote.{0}.fetch'.format(name),
        '+refs/heads/{0}/*:refs/remotes/{1}/*' .format(prefix, name))
    run('git', 'config', 'remote.{0}.push'.format(name),
        '+refs/heads/*:{0}/*'.format(prefix))


def cli_push(verify, remote, verbose, dry_run, ref_globs):
    """
    Push branches and HEAD forcefully to blackhole `remote`.

    Note that local HEAD is pushed to the remote branch named
    ``host/$HOST/$RELPATH/HEAD`` (see help of ``git blackhole init``)
    instead of real remote HEAD.  This way, if the blackhole remote is
    shared with other machine, you can recover the HEAD at ``$HOST``.

    It is useful to call this command from the ``post-commit`` hook::

      nohup git blackhole push --no-verify &> /dev/null &

    To push revisions created by git-wip_ command, add option
    ``--ref-glob='refs/wip/*'``.

    .. _git-wip: https://github.com/bartman/git-wip

    """
    run = make_run(verbose, dry_run, check=False)
    prefix = getprefix('host')
    branches, _checkout = getbranches()

    # Build "git push" command options:
    cmd = ['git', 'push', '--force']
    if verify is True:
        cmd.append('--verify')
    elif verify is False:
        cmd.append('--no-verify')
    cmd.append(remote)
    cmd.extend(branches)
    cmd.extend(refspecs_for_stashes(len(git_stash_list())))
    cmd.extend(refspecs_from_globs(ref_globs))
    # Explicitly specify destination (HEAD:HEAD didn't work):
    cmd.append('HEAD:refs/heads/{0}/HEAD'.format(prefix))

    return run(*cmd)


def cli_trash_branch(branch, remote, remove_upstream, verbose, dry_run):
    """
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

    """
    """
    - FIXME: Maybe I should remove ``$HOST/$RELPATH`` part and use
      branch named ``trash/$REV[:2]/$REV[2:]``, since the JSON has all
      the info I need.
    """
    run = make_run(verbose, dry_run)
    branches, checkout = getbranches()
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
        verbose, dry_run)
    run('git', 'branch', '--delete', '--force', branch)

    if remove_upstream:
        if upstream_repo is None:
            print('Not removing upstream branch as upstream is'
                  ' not configured.')
        else:
            run('git', 'push', upstream_repo, ':' + upstream_branch)


def cli_trash_stash(remote, stash_range, keep_stashes,
                    verbose, dry_run):
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
                verbose, dry_run)
            if not keep_stashes:
                run('git', 'stash', 'drop', stash)


def make_parser(doc=__doc__):
    import argparse

    class FormatterClass(argparse.RawDescriptionHelpFormatter,
                         argparse.ArgumentDefaultsHelpFormatter):
        pass

    parser = argparse.ArgumentParser(
        formatter_class=FormatterClass,
        description=doc)
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

    p = subp('init', cli_init)
    p.add_argument('--name', default='blackhole',
                   help='name of the remote blackhole repository')
    p.add_argument('url',
                   help='URL of the remote blackhole repository')

    p = subp('push', cli_push)
    p.add_argument('--verify', default=None, action='store_true',
                   help='passed to git-push')
    p.add_argument('--no-verify', dest='verify', action='store_false',
                   help='passed to git-push')
    p.add_argument('--remote', default='blackhole',
                   help='name of the remote blackhole repository')
    # FIXME: Stop hard-coding remote name.  Use git config system to
    # set default.
    p.add_argument('--ref-glob', action='append', default=[],
                   dest='ref_globs',
                   help='add glob patterns to be pushed, e.g., wip/*')

    p = subp('trash-branch', cli_trash_branch)
    p.add_argument('branch',
                   help='branch to be removed')
    p.add_argument('--remote', default='blackhole',  # FIXME: see above
                   help='name of the remote blackhole repository')
    p.add_argument('--remove-upstream', '-u', action='store_true',
                   help='remove branch in upstream repository.')

    p = subp('trash-stash', cli_trash_stash)
    p.add_argument('--remote', default='blackhole',  # FIXME: see above
                   help='name of the remote blackhole repository')
    p.add_argument(
        'stash_range',
        help='stashes to trash. It is comma-separated low-high range'
        ' (inclusive). e.g.: 0,3-5,8-')
    p.add_argument(
        '--keep-stashes', '-k', default=False, action='store_true',
        help='when this option is given, do not remove local stashes.')

    return parser


def main(args=None):
    parser = make_parser()
    ns = parser.parse_args(args)
    sys.exit((lambda func, **kwds: func(**kwds))(**vars(ns)))


if __name__ == '__main__':
    main()
