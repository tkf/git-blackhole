import os
import unittest
from subprocess import call, check_call, check_output

import pytest

from .testutils import MixInGitReposPerMethod, MixInGitReposPerClass
from .test_git_tools import commitchange
from git_blackhole import make_run, trash_commitish, trashinfo, gettrashes, \
    git_json_commit, cli_init, cli_trash_branch, cli_trash_stash, \
    cli_fetch_trash, cli_ls_trash, cli_show_trash, cli_rm_local_trash, \
    cli_warp, cli_push, make_parser, main, getprefix, getconfig


run = make_run(True, False)


def git_revision(commitish='HEAD', **kwds):
    kwds.setdefault('universal_newlines', True)
    return check_output(['git', 'rev-parse', '--verify', commitish],
                        **kwds).strip()


def _setUp_home(self):
    self.orig_env = os.environ.copy()
    os.environ.update(HOME=self.tmpdir)

    self.orig_wd = os.getcwd()
    os.chdir(self.tmppath(self.main_repo))


def _tearDown_home(self):
    os.chdir(self.orig_wd)
    os.environ.clear()
    os.environ.update(self.orig_env)


def _setUp_BlackHole(self):
    _setUp_home(self)

    code = cli_init(
        name='blackhole',
        url='../blackhole.git',
        mangle='auto',
        verbose=True,
        dry_run=False)
    assert code in (0, None)
    commitchange()


def _tearDown_BlackHole(self):
    _tearDown_home(self)


class TestInit(MixInGitReposPerMethod, unittest.TestCase):

    other_repos = ['blackhole.git']
    remote = 'blackhole'

    def setUp(self):
        super(TestInit, self).setUp()
        _setUp_home(self)

    def tearDown(self):
        _tearDown_home(self)
        super(TestInit, self).tearDown()

    def cli_init(self, _check=True, **kwds):
        default_kwds = dict(
            verbose=True, dry_run=False,
            name=self.remote,
            url='../blackhole.git',
        )
        code = cli_init(**dict(default_kwds, **kwds))
        if _check:
            assert code is None
        return code

    def is_configured(self):
        config = 'remote.{}.url'.format(self.remote)
        return getconfig(config) is not None

    def test_mangle_auto(self, mangle='auto'):
        self.cli_init(mangle=mangle)
        assert self.is_configured()

    def test_mangle_always(self, mangle='always'):
        self.cli_init(mangle=mangle)
        assert self.is_configured()
        assert getconfig('blackhole.{}.repokey'.format(self.remote))

    def test_mangle_never(self):
        self.test_mangle_auto(mangle='never')

    def test_explicit_repokey(self, **kwargs):
        repokey = 'explicit-repokey'
        self.cli_init(repokey=repokey, **kwargs)
        assert self.is_configured()
        assert getconfig('blackhole.{}.repokey'.format(self.remote)) == repokey


class TestInitInHiddenRepo(TestInit):
    main_repo = '.local'

    def test_mangle_auto(self):
        self.test_mangle_always(mangle='auto')

    def test_mangle_never(self):
        assert self.cli_init(_check=False, mangle='never') != (0, None)
        assert not self.is_configured()

    def test_explicit_repokey_with_auto_mangle(self):
        self.test_explicit_repokey(mangle='auto')


class MixInBlackholePerMethod(MixInGitReposPerMethod):

    other_repos = ['blackhole.git']

    def setUp(self):
        super(MixInBlackholePerMethod, self).setUp()
        _setUp_BlackHole(self)

    def tearDown(self):
        _tearDown_BlackHole(self)
        super(MixInBlackholePerMethod, self).tearDown()


class TestPush(MixInBlackholePerMethod, unittest.TestCase):

    @staticmethod
    def cli_push(_check=True, **kwds):
        default_kwds = dict(
            verbose=True, dry_run=False, ref_globs=[],
            remote='blackhole', skip_if_no_blackhole=False,
        )
        code = cli_push(**dict(default_kwds, **kwds))
        if _check:
            assert code in (0, None)
        return code

    def test_push_head(self):
        local_rev_0 = git_revision()
        blackhole_head = getprefix('heads') + '/HEAD'

        self.cli_push()
        blackhole_rev_0 = git_revision(blackhole_head, cwd='../blackhole.git')
        assert local_rev_0 == blackhole_rev_0

        commitchange()
        local_rev_1 = git_revision()
        assert local_rev_0 != local_rev_1

        self.cli_push()
        blackhole_rev_1 = git_revision(blackhole_head, cwd='../blackhole.git')
        assert local_rev_1 == blackhole_rev_1


class TestTrash(MixInBlackholePerMethod, unittest.TestCase):

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


class TestWarp(MixInBlackholePerMethod, unittest.TestCase):

    other_repos = ['another', 'blackhole.git']

    def setUp(self):
        super(TestWarp, self).setUp()

        cwd = os.getcwd()
        try:
            os.chdir(self.tmppath('another'))
            cli_init(name='blackhole', url='../blackhole.git',
                     verbose=True, dry_run=False)
            commitchange()
            check_call(['git', 'push', 'blackhole', 'master'])
        finally:
            os.chdir(cwd)

    def test_warp(self):
        cli_warp(host='', repokey='another', name='bh_another',
                 remote='blackhole', url='',
                 verbose=True, dry_run=False)
        check_call(['git', 'fetch', 'bh_another'])
        check_call(['git', 'show-ref', '--verify', '--quiet',
                    'refs/remotes/bh_another/master'])


class TestMisc(MixInGitReposPerClass, unittest.TestCase):

    other_repos = ['blackhole.git']

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


class TestCLIUnconfigured(MixInGitReposPerMethod, unittest.TestCase):

    def setUp(self):
        super(TestCLIUnconfigured, self).setUp()
        _setUp_home(self)

    def tearDown(self):
        _tearDown_home(self)
        super(TestCLIUnconfigured, self).tearDown()

    def test_push_no_ignore_error(self):
        with pytest.raises(SystemExit) as excinfo:
            main(['push'])
        assert excinfo.value.code == 1

    def test_push_ignore_error(self):
        main(['push', '--ignore-error'])


class TestPushInHiddenRepo(TestPush):
    main_repo = '.local'


class TestTrashInHiddenRepo(TestTrash):
    main_repo = '.local'


class TestWarpInHiddenRepo(TestWarp):
    main_repo = '.local'


class TestMiscInHiddenRepo(TestMisc):
    main_repo = '.local'


class TestCLIUnconfiguredInHiddenRepo(TestCLIUnconfigured):
    main_repo = '.local'


def get_subcommands():
    parser = make_parser()
    action = parser._subparsers._group_actions[0]
    return action.choices.keys()


@pytest.mark.parametrize('sub_command', [None] + list(get_subcommands()))
def test_argparse_help(sub_command):
    args = ['--help'] if sub_command is None else [sub_command, '--help']
    with pytest.raises(SystemExit) as errinfo:
        main(args)
    assert errinfo.value.code == 0
