from distutils.cmd import Command
import distutils.command.build
import distutils.command.sdist
import distutils.core


class generate_man(Command):
    description = 'Generate man files'

    # Some boilerplate code:
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.spawn([
            'rst2man.py',
            'README.rst',
            'git-blackhole.1'])
        self.spawn([
            'rst2man.py',
            'functional_tests/basic_usage.t',
            'git-blackhole-basic-usage.5'])


class build(distutils.command.build.build):

    sub_commands = [
        ('generate_man', None),
    ] + distutils.command.build.build.sub_commands


class sdist(distutils.command.sdist.sdist):

    sub_commands = [
        ('generate_man', None),
    ] + distutils.command.sdist.sdist.sub_commands

# See also:
# distutils.cmd.get_sub_commands
# https://docs.python.org/distutils/apiref.html#distutils.cmd.Command.sub_commands


def setup(**kwds):
    distutils.core.setup(
        cmdclass={
            'build': build,
            'sdist': sdist,
            'generate_man': generate_man,
        },
        **kwds)
