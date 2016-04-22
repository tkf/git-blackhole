from subprocess import STDOUT, CalledProcessError

import pytest

from git_blackhole import check_communicate


cat_stderr_sh = """\
cat
echo '<stderr>' 1>&2"""

cat_stderr_exit6_sh = cat_stderr_sh + """
exit 6"""


def test_check_communicate_normal():
    assert check_communicate(['cat'], '<stdin>') == b'<stdin>'


def test_check_communicate_redirect_stderr():
    assert check_communicate(
        cat_stderr_sh, '<input>',
        stderr=STDOUT, shell=True) == b'<input><stderr>\n'


def test_check_communicate_fail_with_stderr():
    with pytest.raises(CalledProcessError) as excinfo:
        check_communicate(cat_stderr_exit6_sh, '<input>', shell=True)
    assert excinfo.value.returncode == 6
    assert excinfo.value.output == b'<stderr>\n'


def test_check_communicate_fail_stderr_uncaptured():
    with pytest.raises(CalledProcessError) as excinfo:
        check_communicate(cat_stderr_exit6_sh, '<input>',
                          stderr=None, shell=True)
    assert excinfo.value.returncode == 6
    assert excinfo.value.output == b'<input>'


def test_check_communicate_fail_stderr_redirected():
    with pytest.raises(CalledProcessError) as excinfo:
        check_communicate(cat_stderr_exit6_sh, '<input>',
                          stderr=STDOUT, shell=True)
    assert excinfo.value.returncode == 6
    assert excinfo.value.output == b'<input><stderr>\n'
