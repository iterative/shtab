shtab
=====

- What: Automatically generate shell tab completion scripts for python CLI apps
- Why: Speed & correctness. Alternatives like ``argcomplete`` & ``pyzshcomplete`` are slow and have side-effects
- How: ``shtab`` processes an ``argparse.ArgumentParser`` object to generate a tab completion script for your shell

Usage
~~~~~

.. code:: python

    import argparse
    import shtab, os  # get ready for magic

    def get_main_parser():
        parser = argparse.ArgumentParser(prog="<MY_PROG>", ...)
        parser.add_argument("--install-completion-shell", default="")
        parser.add_subparsers(...)
        ...
        return parser

    if __name__ == "__main__":
        parser = get_main_parser()
        args = parser.parse_args()
        shell = args.install_completion_shell
        if shell:
            assert shell in ("bash", "zsh")
            completion_script = shtab.complete(parser, shell=shell)
            print("Writing to system completion directory...")
            with open(
                os.path.join(
                    os.environ["BASH_COMPLETION_COMPAT_DIR"], "<MY_PROG>.bash"
                ),
                "w",
            ) as fd:
                fd.write(completion_script)
            print("Please restart your terminal.")

Don't want to write any code? Assuming the above example is in
``MY_PROG/command/main.py``, simply run:

.. code:: sh

    python -m shtab --shell bash MY_PROG.command.main.get_main_parser \
      | sudo tee ${BASH_COMPLETION_COMPAT_DIR}/MY_PROG.bash

Or get really meta:

.. code:: sh

    python -m shtab --shell bash shtab.main.get_main_parser \
      | sudo tee ${BASH_COMPLETION_COMPAT_DIR}/MY_PROG.bash


Features
~~~~~~~~

- Supports ``bash`` and ``zsh``
- Supports arguments, options and subcommands (subparsers)
- Supports path completion
