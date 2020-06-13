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

    shtab --shell=bash shtab.main.get_main_parser \
      | sudo tee "$BASH_COMPLETION_COMPAT_DIR"/shtab.bash

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

Assuming this code example is in ``MY_PROG/command/main.py``, simply run:

.. code:: sh

    shtab --shell=bash MY_PROG.command.main.get_main_parser \
      | sudo tee "$BASH_COMPLETION_COMPAT_DIR"/MY_PROG.bash

Configuration
-------------

Alternatively, add direct support to scripts for a little more configurability:

.. code:: python

    import argparse
    import shtab, os  # for completion magic

    def get_main_parser():
        parser = argparse.ArgumentParser(prog="<MY_PROG>", ...)
        parser.add_argument("--install-completion-shell", choices=["bash", "zsh"])
        parser.add_argument("--file", choices=shtab.Optional.FILE)
        parser.add_argument(
            "--dir",
            choices=shtab.Required.DIRECTORY,
            default=os.getenv("BASH_COMPLETION_COMPAT_DIR")
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
            filename = args.file or "<MY_PROG>.bash"
            print("Writing to system completion directory...")
            with open(os.path.join(args.dir, filename), "w") as fd:
                fd.write(completion_script)
            print("Please restart your terminal.")

        ...
