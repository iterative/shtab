#!/usr/bin/env python
"""
`argparse`-based CLI app with custom file completion as well as subparsers.

See `pathcomplete.py` for a more basic version.
"""
import argparse

import shtab  # for completion magic

TXT_FILE = {
    "bash": "_shtab_greeter_compgen_TXTFiles",
    "zsh": "_files -g '(*.txt|*.TXT)'",
}
PREAMBLE = {
    "bash": """
# $1=COMP_WORDS[1]
_shtab_greeter_compgen_TXTFiles() {
  compgen -d -S '/' -- $1  # recurse into subdirs
  compgen -f -X '!*?.txt' -- $1
  compgen -f -X '!*?.TXT' -- $1
}
""",
    "zsh": "",
}


def process(args):
    print(
        "received <input_txt>=%r --input-file=%r --output-name=%r"
        % (args.input_txt, args.input_file, args.output_name)
    )


def get_main_parser():
    main_parser = argparse.ArgumentParser(prog="customcomplete")
    subparsers = main_parser.add_subparsers()
    # make required (py3.7 API change); vis. https://bugs.python.org/issue16308
    subparsers.required = True
    subparsers.dest = "subcommand"

    parser = subparsers.add_parser("completion")
    shtab.add_argument_to(parser, "shell")  # magic!

    parser = subparsers.add_parser("process")
    # `*.txt` file tab completion
    parser.add_argument("input_txt", nargs="?").complete = TXT_FILE
    # file tab completion builtin shortcut
    parser.add_argument("-i", "--input-file").complete = shtab.FILE
    parser.add_argument(
        "-o",
        "--output-name",
        help=(
            "output file name. Completes directory names to avoid users"
            " accidentally overwriting existing files."
        ),
    ).complete = shtab.DIRECTORY  # directory tab completion builtin shortcut
    parser.set_defaults(func=process)
    return main_parser


if __name__ == "__main__":
    parser = get_main_parser()
    args = parser.parse_args()
    args.func(args)
