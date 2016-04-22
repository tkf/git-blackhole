import unittest
from subprocess import check_call

from .testutils import MixInGitRepos
from git_blackhole import getconfig


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
