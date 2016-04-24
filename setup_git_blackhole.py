try:
    from setuptools import setup as setup_orig, Distribution, Command
except ImportError:
    from distutils.core import setup as setup_orig, Distribution, Command

dist = Distribution()
build_orig = dist.get_command_class('build')
sdist_orig = dist.get_command_class('sdist')


class generate_man(Command):
    description = 'Generate man files'

    # Some boilerplate code:
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.spawn(['misc/git-blackhole.1.sh'])
        self.spawn(['misc/git-blackhole-basic-usage.5.sh'])


class build(build_orig):

    sub_commands = [
        ('generate_man', None),
    ] + build_orig.sub_commands


class sdist(sdist_orig):

    sub_commands = [
        ('generate_man', None),
    ] + sdist_orig.sub_commands

# See also:
# distutils.cmd.get_sub_commands
# https://docs.python.org/distutils/apiref.html#distutils.cmd.Command.sub_commands


def setup(**kwds):
    setup_orig(
        cmdclass={
            'build': build,
            'sdist': sdist,
            'generate_man': generate_man,
        },
        **kwds)
