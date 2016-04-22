import unittest
from subprocess import check_call, check_output

from .testutils import MixInGitRepos
from git_blackhole import getconfig, git_annot_commit


def commitchange(file='README', change='change',
                 message='Append "{change}" to "{file}".'):
    with open(file, 'a') as fp:
        fp.write(change)
    check_call(['git', 'add', file])
    check_call(['git', 'commit', '--message', message.format(**locals()),
                '--', file])


class TestGitTools(MixInGitRepos, unittest.TestCase):

    repos = ['repo']

    def test_remote_url(self):
        with self.at('repo'):
            check_call(['git', 'remote', 'add', 'origin', '/dev/null'])
            assert getconfig('remote.origin.url') == '/dev/null'

    def test_multivar(self):
        with self.at('repo'):
            check_call(['git', 'config', '--add', 'spam.egg', 'super'])
            check_call(['git', 'config', '--add', 'spam.egg', 'delicious'])
            assert getconfig('spam.egg', aslist=True) == ['super', 'delicious']

    def test_annot_commit(self):
        with self.at('repo'):
            commitchange()
            check_call(['git', 'checkout', '-b', 'newbranch'])
            commitchange()
            check_call(['git', 'checkout', 'master'])
            rev = git_annot_commit('Annotate newbranch', 'newbranch')
            out = check_output(['git', 'show', rev])
            assert b'Annotate newbranch' in out
