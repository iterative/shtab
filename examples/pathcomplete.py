#!/usr/bin/env python
"""
`argparse`-based CLI app using
`add_argument(choices=shtab.(Optional|Required).(FILE|DIR)`
for file/directory completion.

See `customcomplete.py` for a more advanced version.
"""
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

    # completion magic
    shell = args.print_completion_shell
    if shell:
        print(shtab.complete(parser, shell=shell))
    else:
        print("received --file='%s' --dir='%s'" % (args.file, args.dir))
