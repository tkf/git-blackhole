import os
import unittest
from subprocess import call, check_call, check_output

from .testutils import MixInGitReposPerMethod, MixInGitReposPerClass
from .test_git_tools import commitchange
from git_blackhole import make_run, trash_commitish, trashinfo, gettrashes, \
    git_json_commit, cli_init, cli_trash_branch, cli_trash_stash, \
    cli_fetch_trash, cli_ls_trash, cli_show_trash, cli_rm_local_trash, \
    cli_warp


run = make_run(True, False)


def _setUp_BlackHole(self):
    self.orig_env = os.environ.copy()
    os.environ.update(HOME=self.tmpdir)

    self.orig_wd = os.getcwd()
    os.chdir(self.tmppath('local'))

    cli_init(name='blackhole', url='../blackhole.git',
             verbose=True, dry_run=False)
    commitchange()


def _tearDown_BlackHole(self):
    os.chdir(self.orig_wd)
    os.environ.clear()
    os.environ.update(self.orig_env)


class TestTrash(MixInGitReposPerMethod, unittest.TestCase):

    repos = ['local', 'blackhole.git']

    def setUp(self):
        super(TestTrash, self).setUp()
        _setUp_BlackHole(self)

    def tearDown(self):
        _tearDown_BlackHole(self)
        super(TestTrash, self).tearDown()

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

    def test_trash_branch(self, branch='garbage'):
        run('git', 'branch', branch)
        cli_trash_branch(
            branches=[branch], remove_upstream=False,
            remote='blackhole', verbose=True, dry_run=False)
        assert call(['git', 'show-ref', '--verify', '--quiet', branch]) != 0

    def test_trash_stash(self):
        assert run('git', 'stash', 'list', out=True).decode().strip() == ''

        with open('README', 'a') as file:
            file.write('change')
        run('git', 'stash')

        assert run('git', 'stash', 'list', out=True).decode().strip()
        cli_trash_stash(
            stash_range='0', keep_stashes=False,
            remote='blackhole', verbose=True, dry_run=False)
        assert run('git', 'stash', 'list', out=True).decode().strip() == ''

    def test_fetch_trash(self):
        self.test_trash_branch()
        self.test_trash_stash()
        trashes0 = gettrashes()
        assert len(trashes0) == 0
        cli_fetch_trash(remote='blackhole', verbose=True, dry_run=False)
        trashes2 = gettrashes()
        assert len(trashes2) == 2
        assert set(t['command'] for t in trashes2) == \
            {'trash-branch', 'trash-stash'}

    def test_ls_trash_non_verbose(self):
        self.test_fetch_trash()
        cli_ls_trash(verbose=False, dry_run=False)

    def test_ls_trash_verbose(self):
        self.test_fetch_trash()
        cli_ls_trash(verbose=True, dry_run=False)

    def test_show_trash(self):
        self.test_fetch_trash()
        cli_show_trash(verbose=True, dry_run=False)

    def test_rm_local_trash(self):
        self.test_fetch_trash()
        cli_rm_local_trash(verbose=True, dry_run=False, refs=[], all=True)
        trashes0 = gettrashes()
        assert len(trashes0) == 0


class TestWarp(MixInGitReposPerMethod, unittest.TestCase):

    repos = ['local', 'another', 'blackhole.git']

    def setUp(self):
        super(TestWarp, self).setUp()
        _setUp_BlackHole(self)

        cwd = os.getcwd()
        try:
            os.chdir(self.tmppath('another'))
            cli_init(name='blackhole', url='../blackhole.git',
                     verbose=True, dry_run=False)
            commitchange()
            check_call(['git', 'push', 'blackhole', 'master'])
        finally:
            os.chdir(cwd)

    def tearDown(self):
        _tearDown_BlackHole(self)
        super(TestWarp, self).tearDown()

    def test_warp(self):
        cli_warp(host='', relpath='another', name='bh_another',
                 remote='blackhole', url='',
                 verbose=True, dry_run=False)
        check_call(['git', 'fetch', 'bh_another'])
        check_call(['git', 'show-ref', '--verify', '--quiet',
                    'refs/remotes/bh_another/master'])


class TestMisc(MixInGitReposPerClass, unittest.TestCase):

    repos = ['local', 'blackhole.git']

    @classmethod
    def setUpClass(cls):
        super(TestMisc, cls).setUpClass()
        _setUp_BlackHole(cls)

    @classmethod
    def tearDownClass(cls):
        _tearDown_BlackHole(cls)
        super(TestMisc, cls).tearDownClass()

    def test_read_parse_json_commit(self):
        orig = {'method': 'test_read_parse_json_commit'}
        heading = 'Test commit'
        rev = git_json_commit(heading, orig, 'HEAD')
        parsed0 = trashinfo(rev)
        parsed = parsed0.copy()
        del parsed['rev_info']
        del parsed['rev']
        assert parsed == dict(orig, heading=heading)
