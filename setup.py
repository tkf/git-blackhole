try:
    from setup_git_blackhole import setup
    # This setup.py should work without setup_git_blackhole.py when it
    # is distributed.  The helper module setup_git_blackhole.py is
    # there to automatically generate data files before making
    # distributions.
except ImportError:
    from distutils.core import setup

import git_blackhole


setup(
    name='git-blackhole',
    version=git_blackhole.__version__,
    py_modules=['git_blackhole'],
    data_files=[
        ('share/man/man1', ['git-blackhole.1']),
        ('share/man/man5', ['git-blackhole-basic-usage.5']),
    ],
    author=git_blackhole.__author__,
    author_email='aka.tkf@gmail.com',
    # url='https://github.com/tkf/git_blackhole',
    license=git_blackhole.__license__,
    # description='git_blackhole - THIS DOES WHAT',
    long_description=git_blackhole.__doc__,
    # keywords='KEYWORD, KEYWORD, KEYWORD',
    classifiers=[
        "Development Status :: 3 - Alpha",
        # see: http://pypi.python.org/pypi?%3Aaction=list_classifiers
    ],
    # Having `entry_points` only yields warning for `distutils.core`
    # so let's have it here:
    entry_points={
        'console_scripts': ['git-blackhole = git_blackhole:main'],
    },
    # Since `entry_points` works only with setuptools/pip, use
    # `scripts` as a fall-back:
    scripts=['git-blackhole'],
)
