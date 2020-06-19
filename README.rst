shtab
=====

- What: Automatically generate shell tab completion scripts for python CLI apps
- Why: Speed & correctness. Alternatives like
  `argcomplete <https://pypi.org/project/argcomplete>`_ and
  `pyzshcomplete <https://pypi.org/project/pyzshcomplete>`_ are slow and have
  side-effects
- How: ``shtab`` processes an ``argparse.ArgumentParser`` object to generate a
  tab completion script for your shell

Features
--------

- Outputs completion for

  - ``bash``
  - ``zsh``

- Supports

  - `argparse <https://docs.python.org/library/argparse>`_
  - `docopt <https://pypi.org/project/docopt>`_ (via `argopt <https://pypi.org/project/argopt>`_)

- Supports arguments, options and subparsers
- Supports path completion

.. contents:: Table of contents
   :backlinks: top
   :local:

Installation
------------

- ``pip install shtab``
- ``conda install -c conda-forge shtab``

Usage
-----

The only requirement is that external CLI applications provide an importable
``argparse.ArgumentParser`` object (or alternatively an importable function
which returns a parser object). This may require a trivial code change.

Once that's done, simply add
``eval "$(shtab --shell=bash your_cli_app.your_parser_object)"``
to ``~/.bash_completion`` (assuming ``bash``).

Below are various examples of enabling ``shtab``'s own tab completion scripts.

bash
~~~~

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

    # Install once (will have to re-run if the target's CLI API changes,
    # but doesn't need target to always be in $PYTHONPATH)
    shtab --shell=bash shtab.main.get_main_parser --error-unimportable \
      | sudo tee "$BASH_COMPLETION_COMPAT_DIR"/shtab

zsh
~~~

Note that ``zsh`` requires completion script files to be named ``_{EXECUTABLE}``
(with an underscore prefix).

.. code:: sh

    # Install once (will have to re-run if the target's CLI API changes,
    # but doesn't need target to always be in $PYTHONPATH)
    shtab --shell=zsh shtab.main.get_main_parser --error-unimportable \
      | sudo tee /usr/local/share/zsh/site-functions/_shtab

To be more eager, place the generated script somewhere in ``$fpath``.
For example, at the top of ``.zshrc``:

.. code:: sh

    fpath=($fpath ~/.local)
    shtab --shell=zsh shtab.main.get_main_parser > ~/.local/_shtab

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
        parser = argparse.ArgumentParser(prog="<MY_PROG>", ...)
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
    echo 'eval "$(shtab --shell=bash MY_PROG.command.main.get_main_parser)"' \
      >> ~/.bash_completion

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
application. Use ``--error-unimportable`` to noisily complain.

Advanced Configuration
----------------------

See the `examples/ <https://github.com/iterative/shtab/tree/master/examples>`_
folder for more.

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

- support `fish`
- support `powershell`
- support `tcsh`
