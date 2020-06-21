shtab
=====

|Tests| |Coverage| |Conda| |PyPI|

- What: Automatically generate shell tab completion scripts for python CLI apps
- Why: Speed & correctness. Alternatives like
  `argcomplete <https://pypi.org/project/argcomplete>`_ and
  `pyzshcomplete <https://pypi.org/project/pyzshcomplete>`_ are slow and have
  side-effects
- How: ``shtab`` processes an ``argparse.ArgumentParser`` object to generate a
  tab completion script for your shell

Features
--------

- Outputs tab completion scripts for

  - ``bash``
  - ``zsh``

- Supports

  - `argparse <https://docs.python.org/library/argparse>`_
  - `docopt <https://pypi.org/project/docopt>`_ (via `argopt <https://pypi.org/project/argopt>`_)

- Supports arguments, options and subparsers
- Supports choices (e.g. ``--say={hello,goodbye}``)
- Supports file and directory path completion
- Supports custom path completion (e.g. ``--file={*.txt}``)

------------------------------------------

.. contents:: Table of Contents
   :backlinks: top


Installation
------------

Choose one of:

- ``pip install shtab``
- ``conda install -c conda-forge shtab``

``bash`` users who have never used any kind of tab completion before should also
follow the OS-specific instructions below.

Ubuntu/Debian
~~~~~~~~~~~~~

Recent versions should have completion already enabled. For older versions,
first run ``sudo apt install --reinstall bash-completion``, then make sure these
lines appear in ``~/.bashrc``:

.. code:: sh

    # enable bash completion in interactive shells
    if ! shopt -oq posix; then
     if [ -f /usr/share/bash-completion/bash_completion ]; then
       . /usr/share/bash-completion/bash_completion
     elif [ -f /etc/bash_completion ]; then
       . /etc/bash_completion
     fi
    fi


MacOS
~~~~~

First run ``brew install bash-completion``, then add the following to
``~/.bash_profile``:

.. code:: sh

    if [ -f $(brew --prefix)/etc/bash_completion ]; then
       . $(brew --prefix)/etc/bash_completion
    fi


Usage
-----

The only requirement is that external CLI applications provide an importable
``argparse.ArgumentParser`` object (or alternatively an importable function
which returns a parser object). This may require a trivial code change.

Once that's done, simply put the output of
``shtab --shell=your_shell your_cli_app.your_parser_object`` somewhere your
shell looks for completions.

Below are various examples of enabling ``shtab``'s own tab completion scripts.

bash
~~~~

.. code:: sh

    shtab --shell=bash shtab.main.get_main_parser --error-unimportable \
      | sudo tee "$BASH_COMPLETION_COMPAT_DIR"/shtab

Eager bash
^^^^^^^^^^

If both `shtab` and the module it's completing are globally importable, eager
usage is an option. "Eager" means automatically updating completions each time a
terminal is opened.

.. code:: sh

    # Install locally
    echo 'eval "$(shtab --shell=bash shtab.main.get_main_parser)"' \
      >> ~/.bash_completion

    # Install locally (lazy load for bash-completion>=2.8)
    echo 'eval "$(shtab --shell=bash shtab.main.get_main_parser)"' \
      > "${BASH_COMPLETION_USER_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion}/completions/shtab"

    # Install system-wide
    echo 'eval "$(shtab --shell=bash shtab.main.get_main_parser)"' \
      | sudo tee "$(pkg-config --variable=completionsdir bash-completion)"/shtab

    # Install system-wide (legacy)
    echo 'eval "$(shtab --shell=bash shtab.main.get_main_parser)"' \
      | sudo tee "$BASH_COMPLETION_COMPAT_DIR"/shtab

zsh
~~~

Note that ``zsh`` requires completion script files to be named ``_{EXECUTABLE}``
(with an underscore prefix).

.. code:: sh

    # note the underscore `_` prefix
    shtab --shell=zsh shtab.main.get_main_parser --error-unimportable \
      | sudo tee /usr/local/share/zsh/site-functions/_shtab

Eager zsh
^^^^^^^^^

To be more eager, place the generated script somewhere in ``$fpath``.
For example, add these lines to the top of ``~/.zshrc``:

.. code:: sh

    mkdir -p ~/.zsh/completions
    fpath=($fpath ~/.zsh/completions)  # must be before `compinit` lines
    shtab --shell=zsh shtab.main.get_main_parser > ~/.zsh/completions/_shtab

Examples
--------

See the `examples/ <https://github.com/iterative/shtab/tree/master/examples>`_
folder for more.

Any existing ``argparse``-based scripts should be supported with minimal effort.
For example, starting with this existing code:

.. code:: python

    #!/usr/bin/env python
    import argparse

    def get_main_parser():
        parser = argparse.ArgumentParser(prog="MY_PROG", ...)
        parser.add_argument(...)
        parser.add_subparsers(...)
        ...
        return parser

    if __name__ == "__main__":
        parser = get_main_parser()
        args = parser.parse_args()
        ...

Assuming this code example is installed in ``MY_PROG.command.main``, simply run:

.. code:: sh

    # bash
    shtab --shell=bash -u MY_PROG.command.main.get_main_parser \
      | sudo tee "$BASH_COMPLETION_COMPAT_DIR"/MY_PROG

    # zsh
    shtab --shell=zsh -u MY_PROG.command.main.get_main_parser \
      | sudo tee /usr/local/share/zsh/site-functions/_MY_PROG

FAQs
----

Not working? Make sure that ``shtab`` and the application you're trying to
complete are both accessible from your environment.

"Eager" installation (completions are re-generated upon login/terminal start)
is recommended. Naturally, ``shtab`` and the CLI application to complete should
be accessible/importable from the login environment. If installing ``shtab``
in a different virtual environment, you'd have to add a line somewhere
appropriate (e.g. ``$CONDA_PREFIX/etc/conda/activate.d/env_vars.sh``).

By default, ``shtab`` will silently do nothing if it cannot import the requested
application. Use ``-u, --error-unimportable`` to noisily complain.

Advanced Configuration
----------------------

See the `examples/ <https://github.com/iterative/shtab/tree/master/examples>`_
folder for more.

Complex projects with subparsers and custom completions for paths matching
certain patterns (e.g. ``--file=*.txt``) are fully supported (see
`iterative/dvc:command/completion.py <https://github.com/iterative/dvc/blob/master/dvc/command/completion.py>`_
for example).

Add direct support to scripts for a little more configurability:

.. code:: python

    #!/usr/bin/env python
    import argparse
    import shtab  # for completion magic

    def get_main_parser():
        parser = argparse.ArgumentParser(prog="pathcomplete")
        parser.add_argument(
            "-s", "--print-completion-shell", choices=["bash", "zsh"]
        )
        parser.add_argument(
            "--file",
            choices=shtab.Optional.FILE,  # file tab completion, can be blank
        )
        parser.add_argument(
            "--dir",
            choices=shtab.Required.DIRECTORY,  # directory tab completion
            default=".",
        )
        return parser

    if __name__ == "__main__":
        parser = get_main_parser()
        args = parser.parse_args()
        print("received --file='%s' --dir='%s'" % (args.file, args.dir))

        # completion magic
        shell = args.print_completion_shell
        if shell:
            print(shtab.complete(parser, shell=shell))

docopt
~~~~~~

Simply use `argopt <https://pypi.org/project/argopt>`_ to create a parser
object from `docopt <https://pypi.org/project/docopt>`_ syntax:

.. code:: python

    #!/usr/bin/env python
    """Greetings and partings.

    Usage:
      greeter [options] [<you>] [<me>]

    Options:
      -g, --goodbye  : Say "goodbye" (instead of "hello")
      -b, --print-bash-completion  : Output a bash tab-completion script
      -z, --print-zsh-completion  : Output a zsh tab-completion script

    Arguments:
      <you>  : Your name [default: Anon]
      <me>  : My name [default: Casper]
    """
    import sys, argopt, shtab  # NOQA

    parser = argopt.argopt(__doc__)
    if __name__ == "__main__":
        args = parser.parse_args()
        if args.print_bash_completion:
            print(shtab.complete(parser, shell="bash"))
            sys.exit(0)
        if args.print_zsh_completion:
            print(shtab.complete(parser, shell="zsh"))
            sys.exit(0)

        msg = "k thx bai!" if args.goodbye else "hai!"
        print("{} says '{}' to {}".format(args.me, msg, args.you))

Alternatives
------------

- `argcomplete <https://pypi.org/project/argcomplete>`_

  - executes the underlying script *every* time ``<TAB>`` is pressed (slow and
    has side-effects)
  - only provides ``bash`` completion

- `pyzshcomplete <https://pypi.org/project/pyzshcomplete>`_

  - executes the underlying script *every* time ``<TAB>`` is pressed (slow and
    has side-effects)
  - only provides ``zsh`` completion

- `click <https://pypi.org/project/click>`_

  - different framework completely replacing ``argparse``
  - solves multiple problems (rather than POSIX-style "do one thing well")

Contributions
-------------

Please do open issues & pull requests! Some ideas:

- support ``fish``
- support ``powershell``
- support ``tcsh``

See
`CONTRIBUTING.md <https://github.com/iterative/shtab/tree/master/CONTRIBUTING.md>`_
for more guidance.

|Hits|

.. |Tests| image:: https://github.com/iterative/shtab/workflows/Test/badge.svg
   :target: https://github.com/iterative/shtab/actions
   :alt: Tests

.. |Coverage| image:: https://codecov.io/gh/iterative/shtab/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/iterative/shtab
   :alt: Coverage

.. |Conda| image:: https://img.shields.io/conda/v/conda-forge/shtab.svg?label=conda&logo=conda-forge
   :target: https://anaconda.org/conda-forge/shtab
   :alt: conda-forge

.. |PyPI| image:: https://img.shields.io/pypi/v/shtab.svg?label=pip&logo=PyPI&logoColor=white
   :target: https://pypi.org/project/shtab
   :alt: PyPI

.. |Hits| image:: https://caspersci.uk.to/cgi-bin/hits.cgi?q=shtab&style=social&r=https://github.com/iterative/shtab&a=hidden
   :target: https://caspersci.uk.to/cgi-bin/hits.cgi?q=shtab&a=plot&r=https://github.com/iterative/shtab&style=social
   :alt: Hits
