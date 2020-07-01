#!/usr/bin/env python
"""
`argparse`-based CLI app with custom file completion.

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


def get_main_parser():
    parser = argparse.ArgumentParser(prog="customcomplete")
    parser.add_argument(
        "-s",
        "--print-completion-shell",
        choices=["bash", "zsh"],
        help="prints completion script",
    )
    # `*.txt` file tab completion
    parser.add_argument("input_txt", nargs="?").complete = TXT_FILE
    # "file" tab completion builtin shortcut
    parser.add_argument("-i", "--input-file").complete = "file"
    parser.add_argument(
        "-o",
        "--output-name",
        help=(
            "output file name. Completes directory names to avoid users"
            " accidentally overwriting existing files."
        ),
    ).complete = "directory"  # "directory" tab completion builtin shortcut
    return parser


if __name__ == "__main__":
    parser = get_main_parser()
    args = parser.parse_args()

    # completion magic
    shell = args.print_completion_shell
    if shell:
        script = shtab.complete(parser, shell=shell, preamble=PREAMBLE)
        print(script)
    else:
        print(
            "received <input_txt>=%r --output-dir=%r --output-name=%r"
            % (args.input_txt, args.output_dir, args.output_name)
        )
