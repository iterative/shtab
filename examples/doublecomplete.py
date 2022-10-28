#!/usr/bin/env python
"""
`argparse`-based CLI app with no /-./ completions, only double-hyphen prefixes.
"""
import argparse

import shtab  # for completion magic


def get_main_parser():
    main_parser = argparse.ArgumentParser(prog="doublecomplete", add_help=False)

    shtab.add_argument_to(main_parser, "--shtab-shell", help='shtab')

    main_parser.add_argument('positional1', help='Positional #1')

    main_parser.add_argument('--double-one', help='A double-hyphen option')
    main_parser.add_argument('-s', help=argparse.SUPPRESS)  # A single-hypen option, suppressed

    return main_parser


if __name__ == "__main__":
    parser = get_main_parser()
    args = parser.parse_args()
    print(args)
