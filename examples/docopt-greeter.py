#!/usr/bin/env python
"""Greetings and partings.

Usage:
  greeter [options] [<you>] [<me>]

Options:
  -g, --goodbye  : Say "goodbye" (instead of "hello")
  -b, --print-bash-completion  : Output a bash tab-completion script
  -z, --print-zsh-completion  : Output a zsh tab-completion script

Arguments:
  <you>  : Your name [default: Anon]
  <me>  : My name [default: Casper]
"""
import sys, argopt, shtab  # NOQA

parser = argopt.argopt(__doc__)
if __name__ == "__main__":
    args = parser.parse_args()
    if args.print_bash_completion:
        print(shtab.complete(parser, shell="bash"))
        sys.exit(0)
    if args.print_zsh_completion:
        print(shtab.complete(parser, shell="zsh"))
        sys.exit(0)

    msg = "k thx bai!" if args.goodbye else "hai!"
    print("{} says '{}' to {}".format(args.me, msg, args.you))
