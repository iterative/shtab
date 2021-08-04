from __future__ import print_function

import logging
import re
import sys
from argparse import (
    SUPPRESS,
    Action,
    _AppendAction,
    _AppendConstAction,
    _CountAction,
    _HelpAction,
    _StoreConstAction,
    _VersionAction,
)
from functools import total_ordering

# version detector. Precedence: installed dist, git, 'UNKNOWN'
try:
    from ._dist_ver import __version__
except ImportError:
    try:
        from setuptools_scm import get_version

        __version__ = get_version(root="..", relative_to=__file__)
    except (ImportError, LookupError):
        __version__ = "UNKNOWN"
__all__ = [
    "complete",
    "add_argument_to",
    "SUPPORTED_SHELLS",
    "FILE",
    "DIRECTORY",
    "DIR",
]
log = logging.getLogger(__name__)

SUPPORTED_SHELLS = []
_SUPPORTED_COMPLETERS = {}
CHOICE_FUNCTIONS = {
    "file": {"bash": "_shtab_compgen_files", "zsh": "_files"},
    "directory": {"bash": "_shtab_compgen_dirs", "zsh": "_files -/"},
}
FILE = CHOICE_FUNCTIONS["file"]
DIRECTORY = DIR = CHOICE_FUNCTIONS["directory"]
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


def mark_completer(shell):
    def wrapper(func):
        if shell not in SUPPORTED_SHELLS:
            SUPPORTED_SHELLS.append(shell)
        _SUPPORTED_COMPLETERS[shell] = func
        return func

    return wrapper


def get_completer(shell):
    try:
        return _SUPPORTED_COMPLETERS[shell]
    except KeyError:
        raise NotImplementedError(
            "shell (%s) must be in {%s}" % (shell, ",".join(SUPPORTED_SHELLS))
        )


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


def complete2pattern(opt_complete, shell, choice_type2fn):
    return (
        opt_complete.get(shell, "")
        if isinstance(opt_complete, dict)
        else choice_type2fn[opt_complete]
    )


def replace_format(string, **fmt):
    """Similar to `string.format(**fmt)` but ignores unknown `{key}`s."""
    for k, v in fmt.items():
        string = string.replace("{" + k + "}", v)
    return string


def wordify(string):
    """Replace non-word chars [-. ] with underscores [_]"""
    return string.replace("-", "_").replace(".", " ").replace(" ", "_")


def get_bash_commands(root_parser, root_prefix, choice_functions=None):
    """
    Recursive subcommand parser traversal, returning lists of information on
    commands (formatted for output to the completions script).
    printing bash helper syntax.

    Returns:
      subparsers  : list of subparsers for each parser
      option_strings  : list of options strings for each parser
      compgens  : list of shtab `.complete` functions corresponding to actions
      choices  : list of choices corresponding to actions
      nargs  : list of number of args allowed for each action (if not 0 or 1)
    """
    choice_type2fn = {k: v["bash"] for k, v in CHOICE_FUNCTIONS.items()}
    if choice_functions:
        choice_type2fn.update(choice_functions)

    def get_option_strings(parser):
        """Flattened list of all `parser`'s option strings."""
        return sum(
            (
                opt.option_strings
                for opt in parser._get_optional_actions()
                if opt.help != SUPPRESS
            ),
            [],
        )

    def recurse(parser, prefix):
        """recurse through subparsers, appending to the return lists"""
        subparsers = []
        option_strings = []
        compgens = []
        choices = []
        nargs = []

        # temp lists for recursion results
        sub_subparsers = []
        sub_option_strings = []
        sub_compgens = []
        sub_choices = []
        sub_nargs = []

        # positional arguments
        discovered_subparsers = []
        for i, positional in enumerate(parser._get_positional_actions()):
            if positional.help == SUPPRESS:
                continue

            if hasattr(positional, "complete"):
                # shtab `.complete = ...` functions
                compgens.append(
                    u"{}_pos_{}_COMPGEN={}".format(
                        prefix,
                        i,
                        complete2pattern(positional.complete, "bash", choice_type2fn),
                    )
                )

            if positional.choices:
                # choices (including subparsers & shtab `.complete` functions)
                log.debug("choices:{}:{}".format(prefix, sorted(positional.choices)))

                this_positional_choices = []
                for choice in positional.choices:
                    if isinstance(choice, Choice):
                        # append special completion type to `compgens`
                        # NOTE: overrides `.complete` attribute
                        log.debug(
                            "Choice.{}:{}:{}".format(
                                choice.type, prefix, positional.dest
                            )
                        )
                        compgens.append(
                            u"{}_pos_{}_COMPGEN={}".format(
                                prefix, i, choice_type2fn[choice.type]
                            )
                        )
                    elif isinstance(positional.choices, dict):
                        # subparser, so append to list of subparsers & recurse
                        log.debug("subcommand:%s", choice)
                        if positional.choices[choice].add_help:
                            discovered_subparsers.append(str(choice))
                            this_positional_choices.append(str(choice))
                            (
                                new_subparsers,
                                new_option_strings,
                                new_compgens,
                                new_choices,
                                new_nargs,
                            ) = recurse(
                                positional.choices[choice],
                                prefix + "_" + wordify(choice),
                            )
                            sub_subparsers.extend(new_subparsers)
                            sub_option_strings.extend(new_option_strings)
                            sub_compgens.extend(new_compgens)
                            sub_choices.extend(new_choices)
                            sub_nargs.extend(new_nargs)
                        else:
                            log.debug("skip:subcommand:%s", choice)
                    else:
                        # simple choice
                        this_positional_choices.append(str(choice))

                if this_positional_choices:
                    choices.append(
                        u"{}_pos_{}_choices='{}'".format(
                            prefix, i, " ".join(this_positional_choices)
                        )
                    )

            # skip default `nargs` values
            if positional.nargs not in (None, "1", "?"):
                nargs.append(u"{}_pos_{}_nargs={}".format(prefix, i, positional.nargs))

        if discovered_subparsers:
            subparsers.append(
                u"{}_subparsers=('{}')".format(
                    prefix, "' '".join(discovered_subparsers)
                )
            )
            log.debug("subcommands:{}:{}".format(prefix, discovered_subparsers))

        # optional arguments
        option_strings.append(
            u"{}_option_strings=('{}')".format(
                prefix, "' '".join(get_option_strings(parser))
            )
        )
        for optional in parser._get_optional_actions():
            if optional == SUPPRESS:
                continue

            for option_string in optional.option_strings:
                if hasattr(optional, "complete"):
                    # shtab `.complete = ...` functions
                    compgens.append(
                        u"{}_{}_COMPGEN={}".format(
                            prefix,
                            wordify(option_string),
                            complete2pattern(optional.complete, "bash", choice_type2fn),
                        )
                    )

                if optional.choices:
                    # choices (including shtab `.complete` functions)
                    this_optional_choices = []
                    for choice in optional.choices:
                        # append special completion type to `compgens`
                        # NOTE: overrides `.complete` attribute
                        if isinstance(choice, Choice):
                            log.debug(
                                "Choice.{}:{}:{}".format(
                                    choice.type, prefix, optional.dest
                                )
                            )
                            compgens.append(
                                u"{}_{}_COMPGEN={}".format(
                                    prefix,
                                    wordify(option_string),
                                    choice_type2fn[choice.type],
                                )
                            )
                        else:
                            # simple choice
                            this_optional_choices.append(str(choice))

                    if this_optional_choices:
                        choices.append(
                            u"{}_{}_choices='{}'".format(
                                prefix,
                                wordify(option_string),
                                " ".join(this_optional_choices),
                            )
                        )

                # Check for nargs.
                if optional.nargs is not None and optional.nargs != 1:
                    nargs.append(
                        u"{}_{}_nargs={}".format(
                            prefix, wordify(option_string), optional.nargs
                        )
                    )

        # append recursion results
        subparsers.extend(sub_subparsers)
        option_strings.extend(sub_option_strings)
        compgens.extend(sub_compgens)
        choices.extend(sub_choices)
        nargs.extend(sub_nargs)

        return subparsers, option_strings, compgens, choices, nargs

    return recurse(root_parser, root_prefix)


@mark_completer("bash")
def complete_bash(parser, root_prefix=None, preamble="", choice_functions=None):
    """
    Returns bash syntax autocompletion script.

    See `complete` for arguments.
    """
    root_prefix = wordify("_shtab_" + (root_prefix or parser.prog))
    subparsers, option_strings, compgens, choices, nargs = get_bash_commands(
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

{subparsers}

{option_strings}

{compgens}

{choices}

{nargs}

{preamble}
# $1=COMP_WORDS[1]
_shtab_compgen_files() {
  compgen -f -- $1  # files
}

# $1=COMP_WORDS[1]
_shtab_compgen_dirs() {
  compgen -d -- $1  # recurse into subdirs
}

# $1=COMP_WORDS[1]
_shtab_replace_nonword() {
  echo "${1//[^[:word:]]/_}"
}

# set default values (called for the initial parser & any subparsers)
_set_parser_defaults() {
  local subparsers_var="${prefix}_subparsers[@]"
  subparsers=${!subparsers_var}

  local current_option_strings_var="${prefix}_option_strings[@]"
  current_option_strings=${!current_option_strings_var}

  completed_positional_actions=0

  _set_new_action "pos_${completed_positional_actions}" true
}

# $1=action identifier
# $2=positional action (bool)
# set all identifiers for an action's parameters
_set_new_action() {
  current_action="${prefix}_$(_shtab_replace_nonword $1)"

  local current_action_compgen_var=${current_action}_COMPGEN
  current_action_compgen="${!current_action_compgen_var}"

  local current_action_choices_var="${current_action}_choices"
  current_action_choices="${!current_action_choices_var}"

  local current_action_nargs_var="${current_action}_nargs"
  if [ -n "${!current_action_nargs_var}" ]; then
    current_action_nargs="${!current_action_nargs_var}"
  else
    current_action_nargs=1
  fi

  current_action_args_start_index=$(( $word_index + 1 ))

  current_action_is_positional=$2
}

# Notes:
# `COMPREPLY`: what will be rendered after completion is triggered
# `completing_word`: currently typed word to generate completions for
# `${!var}`: evaluates the content of `var` and expand its content as a variable
#     hello="world"
#     x="hello"
#     ${!x} -> ${hello} -> "world"
{root_prefix}() {
  local completing_word="${COMP_WORDS[COMP_CWORD]}"
  COMPREPLY=()

  prefix={root_prefix}
  word_index=0
  _set_parser_defaults
  word_index=1

  # determine what arguments are appropriate for the current state
  # of the arg parser
  while [ $word_index -ne $COMP_CWORD ]; do
    local this_word="${COMP_WORDS[$word_index]}"

    if [[ -n $subparsers && " ${subparsers[@]} " =~ " ${this_word} " ]]; then
      # valid subcommand: add it to the prefix & reset the current action
      prefix="${prefix}_$(_shtab_replace_nonword $this_word)"
      _set_parser_defaults
    fi

    if [[ " ${current_option_strings[@]} " =~ " ${this_word} " ]]; then
      # a new action should be acquired (due to recognised option string or
      # no more input expected from current action);
      # the next positional action can fill in here
      _set_new_action $this_word false
    fi

    if [[ "$current_action_nargs" != "*" ]] && \\
       [[ "$current_action_nargs" != "+" ]] && \\
       [[ "$current_action_nargs" != *"..." ]] && \\
       (( $word_index + 1 - $current_action_args_start_index >= \\
          $current_action_nargs )); then
      $current_action_is_positional && let "completed_positional_actions += 1"
      _set_new_action "pos_${completed_positional_actions}" true
    fi

    let "word_index+=1"
  done

  # Generate the completions

  if [[ "${completing_word}" == -* ]]; then
    # optional argument started: use option strings
    COMPREPLY=( $(compgen -W "${current_option_strings[*]}" -- "${completing_word}") )
  else
    # use choices & compgen
    COMPREPLY=( $(compgen -W "${current_action_choices}" -- "${completing_word}"; \\
                  [ -n "${current_action_compgen}" ] \\
                  && "${current_action_compgen}" "${completing_word}") )
  fi

  return 0
}

complete -o filenames -F {root_prefix} {prog}""",
        subparsers="\n".join(subparsers),
        option_strings="\n".join(option_strings),
        compgens="\n".join(compgens),
        choices="\n".join(choices),
        nargs="\n".join(nargs),
        preamble=(
            "\n# Custom Preamble\n" + preamble + "\n# End Custom Preamble\n"
            if preamble
            else ""
        ),
        root_prefix=root_prefix,
        prog=parser.prog,
    )


def escape_zsh(string):
    return RE_ZSH_SPECIAL_CHARS.sub(r"\\\1", str(string))


@mark_completer("zsh")
def complete_zsh(parser, root_prefix=None, preamble="", choice_functions=None):
    """
    Returns zsh syntax autocompletion script.

    See `complete` for arguments.
    """
    root_prefix = wordify("_shtab_" + (root_prefix or parser.prog))
    root_arguments = []
    subcommands = {}  # {cmd: {"help": help, "arguments": [arguments]}}

    choice_type2fn = {k: v["zsh"] for k, v in CHOICE_FUNCTIONS.items()}
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
                pattern=complete2pattern(opt.complete, "zsh", choice_type2fn)
                if hasattr(opt, "complete")
                else (
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
        return '"{nargs}:{help}:{pattern}"'.format(
            nargs={"+": "(*)", "*": "(*):"}.get(opt.nargs, ""),
            help=escape_zsh((opt.help or opt.dest).strip().split("\n")[0]),
            pattern=complete2pattern(opt.complete, "zsh", choice_type2fn)
            if hasattr(opt, "complete")
            else (
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
                    arguments.append('"1:Sub command:({})"'.format(" ".join(subsubs)))

                # positionals
                arguments.extend(
                    format_positional(opt)
                    for opt in subparser._get_positional_actions()
                    if not isinstance(opt.choices, dict)
                    if opt.help != SUPPRESS
                )

                subcommands[cmd] = {
                    "help": (subparser.description or "").strip().split("\n")[0],
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
                cmd_orig=cmd, cmd=wordify(cmd), root_prefix=root_prefix
            )
            for cmd in sorted(subcommands)
        ),
        subcommands="\n".join(
            """
{root_prefix}_{cmd}=(
  {arguments}
)""".format(
                root_prefix=root_prefix,
                cmd=wordify(cmd),
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
    parser, shell="bash", root_prefix=None, preamble="", choice_functions=None
):
    """
    parser  : argparse.ArgumentParser
    shell  : str (bash/zsh)
    root_prefix  : str, prefix for shell functions to avoid clashes
      (default: "_{parser.prog}")
    preamble  : dict, mapping shell to text to prepend to generated script
      (e.g. `{"bash": "_myprog_custom_function(){ echo hello }"}`)
    choice_functions  : deprecated.

    N.B. `parser.add_argument().complete = ...` can be used to define custom
    completions (e.g. filenames). See <../examples/pathcomplete.py>.
    """
    if isinstance(preamble, dict):
        preamble = preamble.get(shell, "")
    completer = get_completer(shell)
    return completer(
        parser,
        root_prefix=root_prefix,
        preamble=preamble,
        choice_functions=choice_functions,
    )


def completion_action(parent=None, preamble=""):
    class PrintCompletionAction(Action):
        def __call__(self, parser, namespace, values, option_string=None):
            print(complete(parent or parser, values, preamble=preamble))
            parser.exit(0)

    return PrintCompletionAction


def add_argument_to(
    parser,
    option_string="--print-completion",
    help="print shell completion script",
    parent=None,
    preamble="",
):
    """
    parser  : argparse.ArgumentParser
    option_string  : str or list[str], iff positional (no `-` prefix) then
      `parser` is assumed to actually be a subparser (subcommand mode)
    help  : str
    parent  : argparse.ArgumentParser, required in subcommand mode
    """
    if isinstance(
        option_string, str if sys.version_info[0] > 2 else basestring  # NOQA
    ):
        option_string = [option_string]
    kwargs = {
        "choices": SUPPORTED_SHELLS,
        "default": None,
        "help": help,
        "action": completion_action(parent, preamble),
    }
    if option_string[0][0] != "-":  # subparser mode
        kwargs.update(default=SUPPORTED_SHELLS[0], nargs="?")
        assert parent is not None, "subcommand mode: parent required"
    parser.add_argument(*option_string, **kwargs)
    return parser
