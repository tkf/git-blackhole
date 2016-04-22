# [[[cog import cog; cog.outl('"""\n%s\n"""' % file('README.rst').read())]]]
# [[[end]]]

from __future__ import print_function

import os
from subprocess import check_call, check_output

__version__ = '0.0.0'
__author__ = 'Takafumi Arakaki'
__license__ = None


def getprefix(type):
    from socket import gethostname
    host = gethostname()
    relpath = os.path.relpath(os.getcwd(), os.path.expanduser('~'))
    prefix = '/'.join([type, host, relpath])
    return prefix


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
    out = check_output(['git', 'config', '--null', '--get', name])
    return out.split('\0') if aslist else out.rstrip('\0')


def cli_init(name, url):
    prefix = getprefix('host')
    check_call(['git', 'remote', 'add', name, url])
    check_call(['git', 'config', 'remote.{0}.fetch'.format(name),
                '+refs/heads/{0}/*:refs/remotes/{1}/*' .format(prefix, name)])
    check_call(['git', 'config', 'remote.{0}.push'.format(name),
                '+refs/heads/*:{0}/*'.format(prefix)])


def cli_push(verify, remote, verbose):
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
    cmd.append('HEAD:HEAD')
    if verbose:
        print(*cmd)
    check_call(cmd)


def cli_trash():
    raise NotImplementedError()
    prefix = getprefix('trash')


def cli_trash_branch(branch, remote):
    """
    Push `branch` to trash/$HOST/$RELPATH/$SHA1 and remove `branch` locally.

    - FIXME: record branch name somewhere.
    - FIXME: remove remote branch.
    """
    prefix = getprefix('trash')
    rev = check_output(['git', 'rev-parse', branch]).strip()
    url = getconfig('remote.{0}.url'.format(remote))
    check_call(['git', 'push', url, '{0}:{1}/{2}/{3}'
                .format(branch, prefix, rev[:2], rev[2:])])
    check_call(['git', 'branch', '--delete', '--force', branch])


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

    return parser


def main(args=None):
    parser = make_parser()
    ns = parser.parse_args(args)
    return (lambda func, **kwds: func(**kwds))(**vars(ns))


if __name__ == '__main__':
    main()
