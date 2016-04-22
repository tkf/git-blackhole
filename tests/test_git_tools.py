import unittest
from subprocess import check_call, check_output

from .testutils import MixInGitRepoPerClass, MixInGitRepoPerMethod
from git_blackhole import getconfig, git_annot_commit


def commitchange(file='README', change='change',
                 message='Append "{change}" to "{file}".'):
    with open(file, 'a') as fp:
        fp.write(change)
    check_call(['git', 'add', file])
    check_call(['git', 'commit', '--message', message.format(**locals()),
                '--', file])


class TestGitConfig(MixInGitRepoPerClass, unittest.TestCase):

    def test_remote_url(self):
        check_call(['git', 'remote', 'add', 'origin', '/dev/null'])
        assert getconfig('remote.origin.url') == '/dev/null'

    def test_multivar(self):
        check_call(['git', 'config', '--add', 'spam.egg', 'super'])
        check_call(['git', 'config', '--add', 'spam.egg', 'delicious'])
        assert getconfig('spam.egg', aslist=True) == ['super', 'delicious']

    def test_non_existing_config(self):
        assert getconfig('non.existing.config') is None


class TestGitTools(MixInGitRepoPerMethod, unittest.TestCase):

    def test_annot_commit(self):
        commitchange()
        check_call(['git', 'checkout', '-b', 'newbranch'])
        commitchange()
        check_call(['git', 'checkout', 'master'])
        rev = git_annot_commit('Annotate newbranch', 'newbranch')
        out = check_output(['git', 'show', rev])
        assert b'Annotate newbranch' in out
