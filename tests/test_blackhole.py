import os
import unittest
from subprocess import check_output

from .testutils import MixInGitReposPerMethod
from .test_git_tools import commitchange
from git_blackhole import make_run, cli_init, trash_commitish


run = make_run(True, False)


class TestTrashCommitish(MixInGitReposPerMethod, unittest.TestCase):

    repos = ['local', 'blackhole.git']

    def setUp(self):
        super(TestTrashCommitish, self).setUp()

        self.orig_env = os.environ.copy()
        os.environ.update(HOME=self.tmpdir)

        self.orig_wd = os.getcwd()
        os.chdir(self.tmppath('local'))

        cli_init(name='blackhole', url='../blackhole.git',
                 verbose=True, dry_run=False)
        commitchange()

    def tearDown(self):
        os.chdir(self.orig_wd)
        os.environ.clear()
        os.environ.update(self.orig_env)
        super(TestTrashCommitish, self).tearDown()

    def test_trash_commitish(self):
        run('git', 'checkout', '-b', 'garbage')
        run('git', 'checkout', 'master')
        refspec = trash_commitish(
            'garbage', 'blackhole', {}, 'HEADING',
            verbose=True, dry_run=False)
        revision, bhbranch = refspec.split(':', 1)
        out = check_output(
            ['git', '--git-dir=../blackhole.git', 'show', bhbranch]
        ).decode()
        assert 'HEADING' in out
