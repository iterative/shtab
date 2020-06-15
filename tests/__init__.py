"""
Tests for `shtab`.

Currently runnable via nosetests, e.g.:
    shtab$ nose tests -d -v
"""
from __future__ import absolute_import
import shtab
from .utils import bash_run, bash_compgen


def test_bash():
    bash_run("export FOO=1", '"$FOO" -eq 1')


def test_compgen():
    bash_compgen('-W "foo bar foobar"', "fo", "foo foobar")


def test_choices():
    assert "x" in shtab.Optional.FILE
    assert "" in shtab.Optional.FILE

    assert "x" in shtab.Required.FILE
    assert "" not in shtab.Required.FILE
