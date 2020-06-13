complete
========

- What: Automatically generate shell tab completion scripts for python CLI apps.
- Why: Speed & correctness. Alternatives like ``argcomplete`` & ``pyzshcomplete`` are slow and have side-effects
- How: `complete` will process an ``argparse.ArgumentParser`` object to print out a completion script

Usage
~~~~~

.. code:: python

    import argparse
    import complete, os  # get ready for magic

    if __name__ == "__main__":
        parser = argparse.ArgumentParser(prog="<MY_PROG>", ...)
        parser.add_argument(...)
        parser.add_subparsers(...)
        ...

        args = parser.parse_args()
        ...

        if do_magic:
            completion_script = complete.generate(parser, shell="bash")
            print("Writing to system completion directory...")
            with open(
                os.path.join(
                    os.environ["BASH_COMPLETION_COMPAT_DIR"], "<MY_PROG>.bash"
                ),
                "w",
            ) as fd:
                fd.write(completion_script)
            print("Please restart your terminal.")

Features
~~~~~~~~

- Supports ``bash`` and ``zsh``
- Supports arguments, options and subcommands (subparsers)
- Supports path completion
