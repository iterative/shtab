"""
Tests for `shtab`.

Currently runnable via nosetests, e.g.:
    shtab$ nose tests -d -v
"""
import pytest

import shtab
from shtab.main import get_main_parser
from utils import bash_compgen, bash_run


def test_bash():
    bash_run("export FOO=1", '"$FOO" -eq 1')


def test_compgen():
    bash_compgen('-W "foo bar foobar"', "fo", "foo foobar")


def test_choices():
    assert "x" in shtab.Optional.FILE
    assert "" in shtab.Optional.FILE

    assert "x" in shtab.Required.FILE
    assert "" not in shtab.Required.FILE


@pytest.mark.parametrize("shell", ("bash", "zsh"))
def test_main(shell, caplog):
    parser = get_main_parser()
    print(shtab.complete(parser, shell=shell))
