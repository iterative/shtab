from __future__ import absolute_import
import argparse
from importlib import import_module

from .shtab import complete


def get_main_parser():
    parser = argparse.ArgumentParser(prog="shtab")
    parser.add_argument("parser")
    parser.add_argument("-s", "--shell", default="bash", choices=["bash", "zsh"])
    return parser


def main(argv=None):
    parser = get_main_parser()
    args = parser.parse_args(argv)

    module, other_parser = args.parser.rsplit('.', 1)
    module = import_module(module)
    other_parser = getattr(module, other_parser)
    if callable(other_parser):
        other_parser = other_parser()
    print(complete(other_parser, shell=args.shell))


if __name__ == "__main__":
    main()
