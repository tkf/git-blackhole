import os
import shutil
import subprocess
import tempfile
from contextlib import contextmanager


class MixInTemporaryDirectory(object):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp('.git-blackhole-test')

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def tmppath(self, *subpaths):
        return os.path.join(self.tmpdir, *subpaths)

    @contextmanager
    def at(self, *subpaths):
        orig = os.getcwd()
        cwd = self.tmppath(*subpaths)
        os.chdir(cwd)
        yield cwd
        os.chdir(orig)


class MixInGitRepos(MixInTemporaryDirectory):

    repos = []

    def setUp(self):
        super(MixInGitRepos, self).setUp()
        for repo in self.repos:
            subprocess.check_call(['git', 'init'] + (
                ['--bare'] if repo.endswith('.git') else []
            ) + [repo], cwd=self.tmpdir)
