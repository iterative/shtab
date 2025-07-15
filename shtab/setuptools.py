"""A entry point for setuptools."""
import io
import os
import sys
from contextlib import redirect_stdout, suppress
from importlib import import_module
from importlib.metadata import EntryPoint, EntryPoints
from typing import Callable

from setuptools import Distribution

try:
    import tomllib as tomli
except ImportError:
    import tomli


def get_stdout(function: Callable) -> str:
    """Get stdout."""
    string = io.StringIO()
    with redirect_stdout(string), suppress(SystemExit):
        function()
    string.seek(0)
    content = string.read()
    return content


def generate_completions(distribution: Distribution) -> None:
    """Generate completions."""
    # Get entry_points from setup.py
    entry_points = getattr(distribution, "entry_points")
    if entry_points is None:
        entry_points = EntryPoints()
    entry_points = entry_points.select(group="console_scripts")
    # Get entry_points from setup.cfg
    if len(entry_points) == 0 and os.path.isfile("setup.cfg"):
        import configparser

        parser = configparser.ConfigParser()
        parser.read(["setup.cfg"], encoding="utf-8")
        _entry_points = parser.get("metadata", "entry_points", fallback=None)
        if isinstance(_entry_points, dict):
            console_scripts = _entry_points.get("console_scripts", [])
            for console_script in console_scripts:
                k, _, v = console_script.partition("=")
                entry_points += [
                    EntryPoint(name=k.strip(), group="console_scripts", value=v.strip())]
    # Get entry_points from pyproject.toml
    if len(entry_points) == 0 and os.path.isfile("pyproject.toml"):
        with open("pyproject.toml", "rb") as f:
            pyproject = tomli.load(f)
        scripts = pyproject.get("project", {}).get("scripts", {})
        if isinstance(scripts, dict):
            for k, v in scripts.items():
                entry_points += [EntryPoint(name=k, group="scripts", value=v)]

    cwd = os.getcwd()
    # https://setuptools.pypa.io/en/latest/userguide/package_discovery.html#flat-layout
    sys.path.insert(0, cwd)
    # https://setuptools.pypa.io/en/latest/userguide/package_discovery.html#src-layout
    sys.path.insert(0, os.path.join(cwd, "src"))
    for entry_point in entry_points:
        # entry_point.value can be 'module_path:function_name[extra1, extra2]'
        path = entry_point.value.split("[")[0]
        module_path, _, function_name = path.rpartition(":")
        module = import_module(module_path)
        function = vars(module).get(function_name)
        prog = entry_point.name
        shells = {"bash": prog, "zsh": "_" + prog, "tcsh": prog + ".csh"}
        os.makedirs("sdist", exist_ok=True)
        argv = sys.argv
        for shell, filename in shells.items():
            sys.argv = [prog, "--print-completion", shell]
            # bash, zsh, tcsh only use `\n`
            content = get_stdout(function).replace("\r\n", "\n") # type: ignore
            if content == "":
                continue
            with open(os.path.join("sdist", filename), "w", newline="") as f:
                f.write(content)
        sys.argv = argv
