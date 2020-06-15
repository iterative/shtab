import subprocess


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
