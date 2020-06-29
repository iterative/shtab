# Contributing

## Tests

When contributing pull requests, it's a good idea to run basic checks locally:

```bash
shtab (master)$ pip install .[dev]  # install development dependencies
shtab (master)$ pre-commit install  # install pre-commit checks
shtab (master)$ python -m tests     # run all tests
```

## Layout

Most of the magic lives in [`shtab/__init__.py`](./shtab/__init__.py).

- [shtab/](./shtab/)
  - [`__init__.py`](./shtab/__init__.py)
    - `complete()` - primary API, calls shell-specific versions
    - `complete_bash()`
    - `complete_zsh()`
    - ...
    - `Optional()`, `Required()`, `Choice()` - helpers for advanced completion
      (e.g. dirs, files, `*.txt`)
  - [`main.py`](./shtab/main.py)
    - `get_main_parser()` - returns `shtab`'s own parser object
    - `main()` - `shtab`'s own CLI application

Given that the number of completions a program may need would likely be less
than a million, the focus is on readability rather than premature speed
optimisations.

Helper functions such as `replace_format` allows use of curly braces `{}` in
string snippets without clashing between python's `str.format` and shell
parameter expansion.

The generated shell code itself is also meant to be readable.

## Releases

Tests and deployment are handled automatically by continuous integration. Simply
tag a commit `v{major}.{minor}.{patch}` and wait for a draft release to appear
at <https://github.com/iterative/shtab/releases>. Tidy up the draft's
description before publishing it.

Note that tagging a release is possible by commenting `/tag vM.m.p HASH` in an
issue or PR.
