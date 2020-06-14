from __future__ import absolute_import, print_function
import argparse
from importlib import import_module
import logging

from .shtab import complete

logger = logging.getLogger(__name__)


def get_main_parser():
    parser = argparse.ArgumentParser(prog="shtab")
    parser.add_argument("parser")
    parser.add_argument(
        "-s", "--shell", default="bash", choices=["bash", "zsh"]
    )
    parser.add_argument(
        "-u",
        "--error-unimportable",
        default=False,
        action="store_true",
        help="raise errors if `parser` is not found in $PYTHONPATH",
    )
    return parser


def main(argv=None):
    parser = get_main_parser()
    args = parser.parse_args(argv)

    module, other_parser = args.parser.rsplit(".", 1)
    try:
        module = import_module(module)
    except ImportError as err:
        if args.error_unimportable:
            raise
        logger.debug(str(err))
        return
    other_parser = getattr(module, other_parser)
    if callable(other_parser):
        other_parser = other_parser()
    print(
        complete(
            other_parser,
            shell=args.shell,
            root_prefix=args.parser.split(".", 1)[0],
        )
    )


if __name__ == "__main__":
    main()
