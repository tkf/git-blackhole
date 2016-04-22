# [[[cog import cog; cog.outl('"""\n%s\n"""' % file('README.rst').read())]]]
# [[[end]]]

from __future__ import print_function

import os
import sys
from socket import gethostname
from subprocess import check_call, check_output, CalledProcessError

__version__ = '0.0.0'
__author__ = 'Takafumi Arakaki'
__license__ = None


def getprefix(type):
    host = gethostname()
    relpath = os.path.relpath(os.getcwd(), os.path.expanduser('~'))
    prefix = '/'.join([type, host, relpath])
    return prefix


def getrecinfo():
    return dict(
        host=gethostname(),
        repo=os.getcwd(),
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
    from subprocess import Popen, PIPE
    if 'stderr' not in kwds:
        kwds['stderr'] = PIPE
    proc = Popen(cmd, stdin=PIPE, stdout=PIPE, **kwds)
    if not isinstance(input, bytes):
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
        "GIT-BLACKHOLE: {}\n\n{}".format(heading, json.dumps(obj)),
        parent)


def cli_init(name, url):
    prefix = getprefix('host')
    check_call(['git', 'remote', 'add', name, url])
    check_call(['git', 'config', 'remote.{0}.fetch'.format(name),
                '+refs/heads/{0}/*:refs/remotes/{1}/*' .format(prefix, name)])
    check_call(['git', 'config', 'remote.{0}.push'.format(name),
                '+refs/heads/*:{0}/*'.format(prefix)])


def cli_push(verify, remote, verbose):
    prefix = getprefix('host')
    branches, _checkout = getbranches()
    cmd = ['git', 'push', '--force']
    # --force is necessary due to HEAD:HEAD (except for the first
    # invocation of this command)
    if verify is True:
        cmd.append('--verify')
    elif verify is False:
        cmd.append('--no-verify')
    cmd.append(remote)
    cmd.extend(branches)
    # Explicitly specify destination (HEAD:HEAD didn't work):
    cmd.append('HEAD:refs/heads/{0}/HEAD'.format(prefix))
    if verbose:
        print(*cmd)
    check_call(cmd)


def cli_trash():
    raise NotImplementedError()
    prefix = getprefix('trash')


def cli_trash_branch(branch, remote, remove_upstream):
    """
    Push `branch` to trash/$HOST/$RELPATH/$SHA1 and remove `branch` locally.

    - FIXME: Maybe I should remove ``$HOST/$RELPATH`` part and use
      branch named ``trash/$REV[:2]/$REV[2:]``, since the JSON has all
      the info I need.

    """
    branches, checkout = getbranches()
    if branch == checkout:
        print("Cannot trash the branch '{0}' which you are currently on."
              .format(branch))
        return 1
    prefix = getprefix('trash')
    rev = check_output(['git', 'rev-parse', branch]).strip()
    url = getconfig('remote.{0}.url'.format(remote))
    if remove_upstream:
        upstream_repo = getconfig('branch.{0}.remote'.format(branch))
        upstream_branch = getconfig('branch.{0}.merge'.format(branch))
    info = dict(branch=branch, **getrecinfo())
    heading = 'Trash branch "{branch}" at {host}:{repo}'.format(**info)
    rev = git_json_commit(heading, info, branch)
    check_call(['git', 'push', url, '{0}:refs/heads/{1}/{2}/{3}'
                .format(rev, prefix, rev[:2], rev[2:])])
    check_call(['git', 'branch', '--delete', '--force', branch])

    if remove_upstream:
        if upstream_repo is None:
            print('Not removing upstream branch as upstream is'
                  ' not configured.')
        else:
            check_call(['git', 'push', upstream_repo, ':' + upstream_branch])


def cli_trash_stash():
    raise NotImplementedError()


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
        return p

    p = subp('init', cli_init)
    p.add_argument('--name', default='blackhole')
    p.add_argument('url')

    p = subp('push', cli_push)
    p.add_argument('--verbose', '-v', action='store_true')
    p.add_argument('--verify', default=None, action='store_true')
    p.add_argument('--no-verify', dest='verify', action='store_false')
    p.add_argument('--remote', default='blackhole')
    # FIXME: Stop hard-coding remote name.  Use git config system to
    # set default.

    p = subp('trash', cli_trash)
    p.add_argument

    p = subp('trash-stash', cli_trash_stash)
    p.add_argument

    p = subp('trash-branch', cli_trash_branch)
    p.add_argument('branch')
    p.add_argument('--remote', default='blackhole')  # FIXME: see above
    p.add_argument('--remove-upstream', '-u', action='store_true',
                   help='remove branch in upstream repository.')

    return parser


def main(args=None):
    parser = make_parser()
    ns = parser.parse_args(args)
    sys.exit((lambda func, **kwds: func(**kwds))(**vars(ns)))


if __name__ == '__main__':
    main()
