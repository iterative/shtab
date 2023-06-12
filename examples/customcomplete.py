#!/usr/bin/env python
"""
`argparse`-based CLI app with custom file completion as well as subparsers.

See `pathcomplete.py` for a more basic version.
"""
import argparse

import shtab  # for completion magic

TXT_FILE = {
    "bash": "_shtab_greeter_compgen_TXTFiles", "zsh": "_files -g '(*.txt|*.TXT)'",
    "tcsh": "f:*.txt"}
PREAMBLE = {
    "bash": """
# $1=COMP_WORDS[1]
_shtab_greeter_compgen_TXTFiles() {
  compgen -d -- $1  # recurse into subdirs
  compgen -f -X '!*?.txt' -- $1
  compgen -f -X '!*?.TXT' -- $1
}
""", "zsh": "", "tcsh": ""}


def process(args):
    print(
        "received <input_txt>=%r [<suffix>=%r] --input-file=%r --output-name=%r --hidden-opt=%r" %
        (args.input_txt, args.suffix, args.input_file, args.output_name, args.hidden_opt))


def get_main_parser():
    main_parser = argparse.ArgumentParser(prog="customcomplete")
    subparsers = main_parser.add_subparsers()
    # make required (py3.7 API change); vis. https://bugs.python.org/issue16308
    subparsers.required = True
    subparsers.dest = "subcommand"

    parser = subparsers.add_parser("completion", help="print tab completion")
    shtab.add_argument_to(parser, "shell", parent=main_parser, preamble=PREAMBLE) # magic!

    parser = subparsers.add_parser("process", help="parse files")
    # `*.txt` file tab completion
    parser.add_argument("input_txt", nargs='?').complete = TXT_FILE
    # file tab completion builtin shortcut
    parser.add_argument("-i", "--input-file").complete = shtab.FILE
    parser.add_argument(
        "-o",
        "--output-name",
        help=("output file name. Completes directory names to avoid users"
              " accidentally overwriting existing files."),
    ).complete = shtab.DIRECTORY
    # directory tab completion builtin shortcut

    parser.add_argument("suffix", choices=['json', 'csv'], default='json', nargs='?',
                        help="Output format")
    parser.add_argument("--hidden-opt", action='store_true', help=argparse.SUPPRESS)
    parser.set_defaults(func=process)
    return main_parser


if __name__ == "__main__":
    parser = get_main_parser()
    args = parser.parse_args()
    args.func(args)
