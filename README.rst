shtab
=====

- What: Automatically generate shell tab completion scripts for python CLI apps
- Why: Speed & correctness. Alternatives like ``argcomplete`` & ``pyzshcomplete`` are slow and have side-effects
- How: ``shtab`` processes an ``argparse.ArgumentParser`` object to generate a tab completion script for your shell

Features
~~~~~~~~

- Outputs completion for ``bash`` and ``zsh``
- Supports ``argparse`` and ``docopt`` (via ``argopt``)
- Supports arguments, options and subparsers
- Supports path completion

Usage
~~~~~

Installing ``shtab``'s own tab completion scripts is possible via:

.. code:: sh

    # Install locally (eager)
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

    # zsh equivalent (alternatively place in $fpath/_shtab)
    shtab --shell=zsh shtab.main.get_main_parser --error-unimportable \
      | sudo tee /usr/local/share/zsh/site-functions/_shtab


The same would work for most existing ``argparse``-based scripts.
For example, starting with this existing code:

.. code:: python

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

Configuration
-------------

Alternatively, add direct support to scripts for a little more configurability:

.. code:: python

    import argparse
    import shtab, os  # for completion magic

    def get_main_parser():
        parser = argparse.ArgumentParser(prog="<MY_PROG>", ...)
        parser.add_argument("--install-completion-shell", choices=["bash", "zsh"])
        parser.add_argument(
            "--file",
            choices=shtab.Optional.FILE,  # file tab completion
        )
        parser.add_argument(
            "--dir",
            choices=shtab.Required.DIRECTORY,  # directory tab completion
            default=os.getenv("BASH_COMPLETION_USER_DIR"),
        )
        ...
        return parser

    if __name__ == "__main__":
        parser = get_main_parser()
        args = parser.parse_args()

        # completion magic
        shell = args.install_completion_shell
        if shell:
            completion_script = shtab.complete(parser, shell=shell)
            filename = args.file or "<MY_PROG>"
            print("Writing to system completion directory...")
            with open(os.path.join(args.dir, filename), "w") as fd:
                fd.write(completion_script)
            print("Please restart your terminal.")

        ...

More Examples
-------------

.. code:: python

    #!/usr/bin/env python
    """Greetings and partings.

    Usage:
      greeter [options] [<you>] [<me>]

    Options:
      -b, --bye  : Say "goodbye" (instead of "hello")
      -c, --print-bash-completion  : Output a tab-completion script

    Arguments:
      <you>  : Your name [default: Anon]
      <me>  : My name [default: Casper]
    """
    import sys, argopt, shtab
    parser = argopt.argopt(__doc__)
    if __name__ == "__main__":
        args = parser.parse_args()
        if args.print_bash_completion:
            print(shtab.complete(parser, shell="bash"))
            sys.exit(0)

        msg = "k thx bai!" if args.bye else "hai!"
        print("{} says '{}' to {}".format(args.me, msg, args.you))

Alternatives
------------

- ``argcomplete``

  - executes the underlying script *every* time ``<TAB>`` is pressed (slow and has side-effects)
  - only provides ``bash`` completion

- ``pyzshcomplete``

  - executes the underlying script *every* time ``<TAB>`` is pressed (slow and has side-effects)
  - only provides ``zsh`` completion

- ``click``

  - different framework completely replacing ``argparse``
  - solves multiple problems (rather than POSIX-style "do one thing well")
