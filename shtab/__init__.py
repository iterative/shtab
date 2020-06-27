from __future__ import print_function

import io
import logging
import re
from argparse import (
    SUPPRESS,
    _AppendAction,
    _AppendConstAction,
    _CountAction,
    _HelpAction,
    _StoreConstAction,
    _VersionAction,
)
from functools import total_ordering


def get_version_dist(name=__name__):
    from pkg_resources import DistributionNotFound, get_distribution

    try:
        return get_distribution(name).version
    except DistributionNotFound:
        return "UNKNOWN"


try:
    from setuptools_scm import get_version
except ImportError:
    from os import path

    ROOT = path.abspath(path.dirname(path.dirname(__file__)))
    if path.exists(path.join(ROOT, ".git")):
        __version__ = "UNKNOWN - please install setuptools_scm"
    else:
        __version__ = get_version_dist()
else:
    try:
        __version__ = get_version(root="..", relative_to=__file__)
    except LookupError:
        __version__ = get_version_dist()
__all__ = ["Optional", "Required", "Choice", "complete"]
log = logging.getLogger(__name__)

CHOICE_FUNCTIONS_BASH = {
    "file": "_shtab_compgen_files",
    "directory": "_shtab_compgen_dirs",
}
CHOICE_FUNCTIONS_ZSH = {
    "file": "_files",
    "directory": "_files -/",
}
FLAG_OPTION = (
    _StoreConstAction,
    _HelpAction,
    _VersionAction,
    _AppendConstAction,
    _CountAction,
)
OPTION_END = _HelpAction, _VersionAction
OPTION_MULTI = _AppendAction, _AppendConstAction, _CountAction
RE_ZSH_SPECIAL_CHARS = re.compile(r"([^\w\s.,()-])")  # excessive but safe


@total_ordering
class Choice(object):
    """
    Placeholder to mark a special completion `<type>`.

    >>> ArgumentParser.add_argument(..., choices=[Choice("<type>")])
    """

    def __init__(self, choice_type, required=False):
        """
        See below for parameters.

        choice_type  : internal `type` name
        required  : controls result of comparison to empty strings
        """
        self.required = required
        self.type = choice_type

    def __repr__(self):
        return self.type + ("" if self.required else "?")

    def __cmp__(self, other):
        if self.required:
            return 0 if other else -1
        return 0

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0


class Optional(object):
    """Example: `ArgumentParser.add_argument(..., choices=Optional.FILE)`."""

    FILE = [Choice("file")]
    DIR = DIRECTORY = [Choice("directory")]


class Required(object):
    """Example: `ArgumentParser.add_argument(..., choices=Required.FILE)`."""

    FILE = [Choice("file", True)]
    DIR = DIRECTORY = [Choice("directory", True)]


def replace_format(string, **fmt):
    """Similar to `string.format(**fmt)` but ignores unknown `{key}`s."""
    for k, v in fmt.items():
        string = string.replace("{" + k + "}", v)
    return string


def get_optional_actions(parser):
    """Flattened list of all `parser`'s optional actions."""
    return sum(
        (
            opt.option_strings
            for opt in parser._get_optional_actions()
            if opt.help != SUPPRESS
        ),
        [],
    )


def get_bash_commands(root_parser, root_prefix, choice_functions=None):
    """
    Recursive subcommand parser traversal, printing bash helper syntax.

    Returns:
        subcommands  : list of root_parser subcommands
        options  : list of root_parser options
        script  : str conforming to the output format:

            _{root_parser.prog}_{subcommand}='{options}'
            _{root_parser.prog}_{subcommand}_{subsubcommand}='{options}'
            ...

            # positional file-completion  (e.g. via
            # `add_argument('subcommand', choices=shtab.Required.FILE)`)
            _{root_parser.prog}_{subcommand}_COMPGEN=_shtab_compgen_files
    """
    choice_type2fn = dict(CHOICE_FUNCTIONS_BASH)
    if choice_functions:
        choice_type2fn.update(choice_functions)

    fd = io.StringIO()
    root_options = []

    def recurse(parser, prefix):
        positionals = parser._get_positional_actions()
        commands = []

        if prefix == root_prefix:  # skip root options
            root_options.extend(get_optional_actions(parser))
            log.debug("options: %s", root_options)
        else:
            opts = [
                opt
                for sub in positionals
                if sub.help != SUPPRESS
                if sub.choices
                for opt in sub.choices
                if not isinstance(opt, Choice)
            ]
            opts += get_optional_actions(parser)
            # use list rather than set to maintain order
            opts = " ".join(opts)
            print("{}='{}'".format(prefix, opts), file=fd)

        for sub in positionals:
            if sub.choices:
                log.debug("choices:{}:{}".format(prefix, sorted(sub.choices)))
                for cmd in sorted(sub.choices):
                    if isinstance(cmd, Choice):
                        log.debug(
                            "Choice.{}:{}:{}".format(
                                cmd.type, prefix, sub.dest
                            )
                        )
                        print(
                            "{}_COMPGEN={}".format(
                                prefix, choice_type2fn[cmd.type]
                            ),
                            file=fd,
                        )
                    else:
                        assert isinstance(sub.choices, dict)
                        log.debug("subcommand:%s", cmd)
                        if sub.choices[cmd].add_help:
                            commands.append(cmd)
                            recurse(
                                sub.choices[cmd],
                                prefix + "_" + cmd.replace("-", "_"),
                            )
                        else:
                            log.debug("skip:subcommand:%s", cmd)
            else:
                log.debug("uncompletable:{}:{}".format(prefix, sub.dest))

        if commands:
            log.debug("subcommands:{}:{}".format(prefix, commands))
        return commands

    return recurse(root_parser, root_prefix), root_options, fd.getvalue()


def complete_bash(
    parser, root_prefix=None, preamble="", choice_functions=None,
):
    """
    Returns bash syntax autocompletion script.

    See `complete` for arguments.
    """
    root_prefix = "_shtab_" + (root_prefix or parser.prog)
    commands, options, subcommands_script = get_bash_commands(
        parser, root_prefix, choice_functions=choice_functions
    )

    # References:
    # - https://www.gnu.org/software/bash/manual/html_node/
    #   Programmable-Completion.html
    # - https://opensource.com/article/18/3/creating-bash-completion-script
    # - https://stackoverflow.com/questions/12933362
    return replace_format(
        """\
#!/usr/bin/env bash
# AUTOMATCALLY GENERATED by `shtab`

{root_prefix}_options_='{options}'
{root_prefix}_commands_='{commands}'

{subcommands}
{preamble}
# $1=COMP_WORDS[1]
_shtab_compgen_files() {
  compgen -f -- $1  # files
  compgen -d -S '/' -- $1  # recurse into subdirs
}

# $1=COMP_WORDS[1]
_shtab_compgen_dirs() {
  compgen -d -S '/' -- $1  # recurse into subdirs
}

# $1=COMP_WORDS[1]
_shtab_replace_hyphen() {
  echo $1 | sed 's/-/_/g'
}

# $1=COMP_WORDS[1]
{root_prefix}_compgen_root_() {
  local args_gen="{root_prefix}_COMPGEN"
  case "$word" in
    -*) COMPREPLY=( $(compgen -W "${root_prefix}_options_" -- "$word"; \
[ -n "${!args_gen}" ] && ${!args_gen} "$word") ) ;;
    *) COMPREPLY=( $(compgen -W "${root_prefix}_commands_" -- "$word"; \
[ -n "${!args_gen}" ] && ${!args_gen} "$word") ) ;;
  esac
}

# $1=COMP_WORDS[1]
{root_prefix}_compgen_command_() {
  local flags_list="{root_prefix}_$(_shtab_replace_hyphen $1)"
  local args_gen="${flags_list}_COMPGEN"
  COMPREPLY=( $(compgen -W "${!flags_list}" -- "$word"; \
[ -n "${!args_gen}" ] && ${!args_gen} "$word") )
}

# $1=COMP_WORDS[1]
# $2=COMP_WORDS[2]
{root_prefix}_compgen_subcommand_() {
  local flags_list="{root_prefix}_$(\
_shtab_replace_hyphen $1)_$(_shtab_replace_hyphen $2)"
  local args_gen="${flags_list}_COMPGEN"
  [ -n "${!args_gen}" ] && local opts_more="$(${!args_gen} "$word")"
  local opts="${!flags_list}"
  if [ -z "$opts$opts_more" ]; then
    {root_prefix}_compgen_command_ $1
  else
    COMPREPLY=( $(compgen -W "$opts" -- "$word"; \
[ -n "$opts_more" ] && echo "$opts_more") )
  fi
}

# Notes:
# `COMPREPLY` contains what will be rendered after completion is triggered
# `word` refers to the current typed word
# `${!var}` is to evaluate the content of `var`
# and expand its content as a variable
#       hello="world"
#       x="hello"
#       ${!x} ->  ${hello} ->  "world"
{root_prefix}() {
  local word="${COMP_WORDS[COMP_CWORD]}"

  COMPREPLY=()

  if [ "${COMP_CWORD}" -eq 1 ]; then
    {root_prefix}_compgen_root_ ${COMP_WORDS[1]}
  elif [ "${COMP_CWORD}" -eq 2 ]; then
    {root_prefix}_compgen_command_ ${COMP_WORDS[1]}
  elif [ "${COMP_CWORD}" -ge 3 ]; then
    {root_prefix}_compgen_subcommand_ ${COMP_WORDS[1]} ${COMP_WORDS[2]}
  fi

  return 0
}

complete -o nospace -F {root_prefix} {prog}""",
        commands=" ".join(commands),
        options=" ".join(options),
        preamble=(
            "\n# Custom Preamble\n" + preamble + "\n# End Custom Preamble\n"
            if preamble
            else ""
        ),
        prog=parser.prog,
        root_prefix=root_prefix,
        subcommands=subcommands_script,
    )


def escape_zsh(string):
    return RE_ZSH_SPECIAL_CHARS.sub(r"\\\1", string)


def complete_zsh(parser, root_prefix=None, preamble="", choice_functions=None):
    """
    Returns zsh syntax autocompletion script.

    See `complete` for arguments.
    """
    root_prefix = "_shtab_" + (root_prefix or parser.prog)

    root_arguments = []
    subcommands = {}  # {cmd: {"help": help, "arguments": [arguments]}}

    choice_type2fn = dict(CHOICE_FUNCTIONS_ZSH)
    if choice_functions:
        choice_type2fn.update(choice_functions)

    def format_optional(opt):
        return (
            (
                '{nargs}{options}"[{help}]"'
                if isinstance(opt, FLAG_OPTION)
                else '{nargs}{options}"[{help}]:{dest}:{pattern}"'
            )
            .format(
                nargs=(
                    '"(- :)"'
                    if isinstance(opt, OPTION_END)
                    else '"*"'
                    if isinstance(opt, OPTION_MULTI)
                    else ""
                ),
                options=(
                    "{{{}}}".format(",".join(opt.option_strings))
                    if len(opt.option_strings) > 1
                    else '"{}"'.format("".join(opt.option_strings))
                ),
                help=escape_zsh(opt.help or ""),
                dest=opt.dest,
                pattern=(
                    choice_type2fn[opt.choices[0].type]
                    if isinstance(opt.choices[0], Choice)
                    else "({})".format(" ".join(opt.choices))
                )
                if opt.choices
                else "",
            )
            .replace('""', "")
        )

    def format_positional(opt):
        return '"{nargs}:{help}:{choices}"'.format(
            nargs={"+": "*", "*": "*"}.get(opt.nargs, ""),
            help=escape_zsh((opt.help or opt.dest).strip().split("\n")[0]),
            choices=(
                choice_type2fn[opt.choices[0].type]
                if isinstance(opt.choices[0], Choice)
                else "({})".format(" ".join(opt.choices))
            )
            if opt.choices
            else "",
        )

    for sub in parser._get_positional_actions():
        if not sub.choices or not isinstance(sub.choices, dict):
            # positional argument
            opt = sub
            if opt.help != SUPPRESS:
                root_arguments.append(format_positional(opt))
        else:  # subparser
            log.debug("choices:{}:{}".format(root_prefix, sorted(sub.choices)))
            for cmd, subparser in sub.choices.items():
                if not subparser.add_help:
                    log.debug("skip:subcommand:%s", cmd)
                    continue
                log.debug("subcommand:%s", cmd)

                # optionals
                arguments = [
                    format_optional(opt)
                    for opt in subparser._get_optional_actions()
                    if opt.help != SUPPRESS
                ]

                # subcommand positionals
                subsubs = sum(
                    (
                        list(opt.choices)
                        for opt in subparser._get_positional_actions()
                        if isinstance(opt.choices, dict)
                    ),
                    [],
                )
                if subsubs:
                    arguments.append(
                        '"1:Sub command:({})"'.format(" ".join(subsubs))
                    )

                # positionals
                arguments.extend(
                    format_positional(opt)
                    for opt in subparser._get_positional_actions()
                    if not isinstance(opt.choices, dict)
                    if opt.help != SUPPRESS
                )

                subcommands[cmd] = {
                    "help": (subparser.description or "")
                    .strip()
                    .split("\n")[0],
                    "arguments": arguments,
                }
                log.debug("subcommands:%s:%s", cmd, subcommands[cmd])

    log.debug("subcommands:%s:%s", root_prefix, sorted(subcommands))

    # References:
    #   - https://github.com/zsh-users/zsh-completions
    #   - http://zsh.sourceforge.net/Doc/Release/Completion-System.html
    #   - https://mads-hartmann.com/2017/08/06/
    #     writing-zsh-completion-scripts.html
    #   - http://www.linux-mag.com/id/1106/
    return replace_format(
        """\
#compdef {prog}

# AUTOMATCALLY GENERATED by `shtab`

{root_prefix}_options_=(
  {root_options}
)

{root_prefix}_commands_() {
  local _commands=(
    {commands}
  )

  _describe '{prog} commands' _commands
}
{subcommands}
{preamble}
typeset -A opt_args
local context state line curcontext="$curcontext"

_arguments \\
  ${root_prefix}_options_ \\
  {root_arguments} \\
  ': :{root_prefix}_commands_' \\
  '*::args:->args'

case $words[1] in
  {commands_case}
esac""",
        root_prefix=root_prefix,
        prog=parser.prog,
        commands="\n    ".join(
            '"{}:{}"'.format(cmd, escape_zsh(subcommands[cmd]["help"]))
            for cmd in sorted(subcommands)
        ),
        root_arguments=" \\\n  ".join(root_arguments),
        root_options="\n  ".join(
            format_optional(opt)
            for opt in parser._get_optional_actions()
            if opt.help != SUPPRESS
        ),
        commands_case="\n  ".join(
            "{cmd_orig}) _arguments ${root_prefix}_{cmd} ;;".format(
                cmd_orig=cmd,
                cmd=cmd.replace("-", "_"),
                root_prefix=root_prefix,
            )
            for cmd in sorted(subcommands)
        ),
        subcommands="\n".join(
            """
{root_prefix}_{cmd}=(
  {arguments}
)""".format(
                root_prefix=root_prefix,
                cmd=cmd.replace("-", "_"),
                arguments="\n  ".join(subcommands[cmd]["arguments"]),
            )
            for cmd in sorted(subcommands)
        ),
        preamble=(
            "\n# Custom Preamble\n" + preamble + "\n# End Custom Preamble\n"
            if preamble
            else ""
        ),
    )


def complete(
    parser, shell="bash", root_prefix=None, preamble="", choice_functions=None,
):
    """
    parser  : argparse.ArgumentParser
    shell  : str (bash/zsh)
    root_prefix  : str, prefix for shell functions to avoid clashes
      (default: "_{parser.prog}")
    preamble  : str, prepended to generated script
    choice_functions  : dict, maps custom `shtab.Choice.type`s to
      completion functions (possibly defined in `preamble`)
    """
    if shell == "bash":
        return complete_bash(
            parser,
            root_prefix=root_prefix,
            preamble=preamble,
            choice_functions=choice_functions,
        )
    if shell == "zsh":
        return complete_zsh(
            parser,
            root_prefix=root_prefix,
            preamble=preamble,
            choice_functions=choice_functions,
        )
    raise NotImplementedError(shell)
