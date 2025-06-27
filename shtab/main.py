import argparse
import contextlib
import logging
import os
import sys
from importlib import import_module
from pathlib import Path
from typing import Generator
from typing import Optional as Opt
from typing import TextIO

from . import SUPPORTED_SHELLS, __version__, add_argument_to, complete

log = logging.getLogger(__name__)


@contextlib.contextmanager
def extract_stdout(output: Opt[Path]) -> Generator[TextIO, None, None]:
    if output is None:
        yield sys.stdout
    else:
        with output.open("w") as stdout:
            yield stdout


def get_main_parser():
    parser = argparse.ArgumentParser(prog="shtab")
    parser.add_argument("parser", help="importable parser (or function returning parser)")
    parser.add_argument("--version", action="version", version="%(prog)s " + __version__)
    parser.add_argument("-s", "--shell", default=SUPPORTED_SHELLS[0], choices=SUPPORTED_SHELLS)
    parser.add_argument("-o", "--output", help="write output to file instead of stdout", type=Path)
    parser.add_argument("--prefix", help="prepended to generated functions to avoid clashes")
    parser.add_argument("--preamble", help="prepended to generated script")
    parser.add_argument("--prog", help="custom program name (overrides `parser.prog`)")
    parser.add_argument(
        "-u",
        "--error-unimportable",
        default=False,
        action="store_true",
        help="raise errors if `parser` is not found in $PYTHONPATH",
    )
    parser.add_argument("--verbose", dest="loglevel", action="store_const", default=logging.INFO,
                        const=logging.DEBUG, help="Log debug information")
    add_argument_to(parser, "--print-own-completion", help="print shtab's own completion")
    return parser


def main(argv=None):
    parser = get_main_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=args.loglevel)
    log.debug(args)

    module, other_parser = args.parser.rsplit(".", 1)
    if sys.path and sys.path[0]:
        # not blank so not searching curdir
        sys.path.insert(1, os.curdir)
    try:
        module = import_module(module)
    except ImportError as err:
        if args.error_unimportable:
            raise
        log.debug(str(err))
        return
    other_parser = getattr(module, other_parser)
    if callable(other_parser):
        other_parser = other_parser()
    if args.prog:
        other_parser.prog = args.prog
    with extract_stdout(args.output) as stdout:
        print(
            complete(other_parser, shell=args.shell, root_prefix=args.prefix
                     or args.parser.split(".", 1)[0], preamble=args.preamble), file=stdout)
