"""
Tests for `shtab`.

Currently runnable via nosetests, e.g.:
    shtab$ nose tests -d -v
"""
import logging
import subprocess

import pytest

import shtab
from shtab.main import get_main_parser


def bash_run(init="", test="1", failure_message=""):
    """Equivalent to `bash -c '{init}; [[ {test} ]]'`."""
    init = init + "\n" if init else ""
    proc = subprocess.Popen(
        ["bash", "-c", "{init}[[ {test} ]]".format(init=init, test=test)]
    )
    stdout, stderr = proc.communicate()
    assert (
        0 == proc.wait()
    ), """\
{}
{}
=== stdout ===
{}=== stderr ===
{}""".format(
        failure_message, test, stdout or "", stderr or ""
    )


def bash_compgen(compgen_cmd, word, expected_completions, init="", msg=""):
    bash_run(
        init,
        '"$(compgen {} -- {} |xargs)" = "{}"'.format(
            compgen_cmd, word, expected_completions
        ),
        msg,
    )


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
    with caplog.at_level(logging.INFO):
        print(shtab.complete(parser, shell=shell))
    assert not caplog.record_tuples
