__all__ = ["Optional", "Required", "complete"]


class Choice(object):
    """
    Placeholder, usage:
    >>> ArgumentParser.add_argument(..., choices=[Choice("<type>")])
    to mark a special completion `<type>`.
    """
    def __init__(self, name, required=False):
        self.required = required
        self.type = name

    def __cmp__(self, other):
        if self.required:
            return 0 if other else -1
        return 0


class Optional(object):
    """Example: `ArgumentParser.add_argument(..., choices=Optional.FILE)`"""
    FILE = [Choice("file")]
    DIR = DIRECTORY = [Choice("directory")]


class Required(object):
    """Example: `ArgumentParser.add_argument(..., choices=Required.FILE)`"""
    FILE = [Choice("file", True)]
    DIR = DIRECTORY = [Choice("directory", True)]


def complete(parser, shell="bash", **kwargs):
    print(str((shell, kwargs, parser)))
