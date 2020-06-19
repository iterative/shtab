#!/usr/bin/env python
"""
`argparse`-based CLI app with custom file completion.

See `pathcomplete.py` for a more basic version.
"""
import argparse

import shtab  # for completion magic

CHOICE_FUNCTIONS = {
    "bash": {"*.txt": "_shtab_greeter_compgen_TXTFiles"},
    "zsh": {"*.txt": "_files -g '(*.txt|*.TXT)'"},
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


class Optional(shtab.Required):
    TXT_FILE = [shtab.Choice("*.txt", required=False)]


class Required(shtab.Required):
    TXT_FILE = [shtab.Choice("*.txt", required=True)]


def get_main_parser():
    parser = argparse.ArgumentParser(prog="customcomplete")
    parser.add_argument(
        "-s", "--print-completion-shell", choices=["bash", "zsh"]
    )
    parser.add_argument(
        "-o",
        "--output-txt",
        choices=Optional.TXT_FILE,  # *.txt file tab completion, can be blank
    )
    parser.add_argument(
        "input_txt", choices=Required.TXT_FILE,  # cannot be blank
    )
    return parser


if __name__ == "__main__":
    parser = get_main_parser()
    args = parser.parse_args()

    # completion magic
    shell = args.print_completion_shell
    if shell:
        script = shtab.complete(
            parser,
            shell=shell,
            preamble=PREAMBLE[shell],
            choice_functions=CHOICE_FUNCTIONS[shell],
        )
        print(script)
    else:
        print(
            "received input_txt='%s' --output-txt='%s'"
            % (args.input_txt, args.output_txt)
        )
