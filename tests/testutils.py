import os
import shutil
import subprocess
import tempfile
from contextlib import contextmanager


class BaseMixInTempDir(object):

    @contextmanager
    def at(self, *subpaths):
        orig = os.getcwd()
        cwd = self.tmppath(*subpaths)
        os.chdir(cwd)
        yield cwd
        os.chdir(orig)


def _setUp_TempDir(self):
    self.tmpdir = tempfile.mkdtemp(prefix='git-blackhole-test-')


def _tearDown_TempDir(self):
    shutil.rmtree(self.tmpdir)


def _tmppath(self, *subpaths):
    return os.path.join(self.tmpdir, *subpaths)


class MixInTempDirPerMethod(BaseMixInTempDir):
    setUp = _setUp_TempDir
    tearDown = _tearDown_TempDir
    tmppath = _tmppath


class MixInTempDirPerClass(BaseMixInTempDir):
    setUpClass = classmethod(_setUp_TempDir)
    tearDownClass = classmethod(_tearDown_TempDir)
    tmppath = classmethod(_tmppath)


def _prepare_repo(self, repo):
    subprocess.check_call(['git', 'init'] + (
        ['--bare'] if repo.endswith('.git') else []
    ) + [repo], cwd=self.tmpdir)

    for cmd in [
            ['git', 'config', 'user.email', 'test@blackhole'],
            ['git', 'config', 'user.name', 'Test Black-Hole'],
    ]:
        subprocess.check_call(cmd, cwd=self.tmppath(repo))


def _setUp_GitRepo(self):
    _prepare_repo(self, self.repo)
    self.orig = os.getcwd()
    cwd = self.tmppath(self.repo)
    os.chdir(cwd)


def _tearDown_GitRepo(self):
    os.chdir(self.orig)


class MixInGitRepoPerMethod(MixInTempDirPerMethod):

    repo = 'repo'

    def setUp(self):
        super(MixInGitRepoPerMethod, self).setUp()
        _setUp_GitRepo(self)

    def tearDown(self):
        _tearDown_GitRepo(self)
        super(MixInGitRepoPerMethod, self).tearDown()


class MixInGitRepoPerClass(MixInTempDirPerClass):

    repo = 'repo'

    @classmethod
    def setUpClass(cls):
        super(MixInGitRepoPerClass, cls).setUpClass()
        _setUp_GitRepo(cls)

    @classmethod
    def tearDownClass(cls):
        _tearDown_GitRepo(cls)
        super(MixInGitRepoPerClass, cls).tearDownClass()


def _setUp_GitRepos(self):
    for repo in self.get_repos():
        _prepare_repo(self, repo)


class BaseGitRepos(object):

    main_repo = 'local'
    other_repos = []

    @classmethod
    def get_repos(self):
        return [self.main_repo] + self.other_repos


class MixInGitReposPerMethod(MixInTempDirPerMethod, BaseGitRepos):

    def setUp(self):
        super(MixInGitReposPerMethod, self).setUp()
        _setUp_GitRepos(self)


class MixInGitReposPerClass(MixInTempDirPerClass, BaseGitRepos):

    @classmethod
    def setUpClass(cls):
        super(MixInGitReposPerClass, cls).setUpClass()
        _setUp_GitRepos(cls)
