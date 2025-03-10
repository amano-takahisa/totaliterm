#!/usr/bin/env python3
"""Execute a command on multiple git repositories."""

import pathlib
import subprocess

import click
import tomlkit
import tomlkit.items
import tomlkit.toml_file
from rich import pretty
from rich.console import Console
from rich.style import Style

pretty.install()

# path to a config file in $XDG_CONFIG_HOME/totaliterm/config or
# ~/.config/totaliterm/config or ~/.totaliterm/config
CONFIG_FILE_PATH = pathlib.Path(click.get_app_dir('totaliterm')).joinpath(
    'config.toml'
)
if not CONFIG_FILE_PATH.exists():
    CONFIG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE_PATH.touch()


@click.group(
    help='Execute a command on multiple directories.',
)
def main() -> None:
    """Execute a command on multiple directories."""


@main.command(
    help='Add directories to the configuration file.',
)
@click.argument(
    'path',
    nargs=-1,
    type=pathlib.Path,
)
@click.option(
    '-t',
    '--tag',
    type=str,
    default='default',
    show_default=True,
    help='tag of directories.',
)
def add(
    path: tuple[pathlib.Path],
    tag: str = 'default',
) -> None:
    """Add directories to the configuration file."""
    config_file = tomlkit.toml_file.TOMLFile(CONFIG_FILE_PATH)
    doc = config_file.read()
    dir_table: tomlkit.items.Table = doc.get('directories', tomlkit.table())
    doc.update({'directories': dir_table})
    dir_array: tomlkit.items.Array = dir_table.get(
        tag, tomlkit.array()
    ).multiline(multiline=True)
    dir_table[tag] = dir_array
    for p in path:
        if not p.exists():
            click.echo(f'{p} does not exist.')
            continue
        if not p.is_dir():
            click.echo(f'{p} is not a directory.')
            continue
        if p.resolve().as_posix() in dir_array:
            click.echo(f'{p} is already in the list.')
            continue
        dir_array.append(p.resolve().as_posix())
    config_file.write(doc)
    list_dirs(
        tag=tag,
        show_all_tags=False,
        list_one_per_line=False,
    )


@main.group()
def second_level_2() -> None:
    """Second level 2."""


@second_level_2.command()
def third_level_command_3() -> None:
    """Third level command under 2nd level 2."""


@main.command(
    help='Execute a command at the each directory.',
)
@click.option(
    '-c',
    '--command',
    type=str,
    required=True,
    help='Any arbitrary command you want to execute in the directory. '
    'Command need to be given as a string, for example, '
    "'ls -lha'.",
)
@click.option(
    '-s',
    '--skip',
    'skip',
    type=str,
    default='',
    help='Skip directories. Give indices of directories to skip.'
    "For example, '-s 1,3'.",
)
@click.option(
    '-t',
    '--tag',
    type=str,
    default='default',
    show_default=True,
    help='tag of directories.',
)
@click.option(
    '-y',
    '--yes',
    is_flag=True,
    help='Execute the command without confirmation.',
)
def run(
    command: str,
    *,
    tag: str = 'default',
    yes: bool = False,
    skip: str = '',
) -> None:
    """Any arbitrary command you want to execute in the directory."""
    console = Console()
    skip_list = [int(i) for i in skip.split(',') if i]
    for i, dir_ in enumerate(
        tomlkit.toml_file.TOMLFile(CONFIG_FILE_PATH).read()['directories'][tag]
    ):
        if i + 1 in skip_list:
            console.print(f'{i + 1}: {dir_}', style=Style(dim=True))
            console.print('  Skipped.', style=Style(dim=True))
            continue
        console.print(f'{i + 1}: {dir_}')
        if not yes and not click.confirm(
            f'Run the following command?\n  $ {command} ',
            default=True,
        ):
            continue
        cmd = command.split()
        # run cmd and show standard output and standard error
        subprocess.run(cmd, cwd=dir_, check=False)  # noqa: S603


def get_tags(
    dir_path: pathlib.Path, dir_table: tomlkit.items.Table
) -> list[str]:
    """Get tags of a directory."""
    tags = []
    for tag, dir_array in dir_table.items():
        if dir_path.resolve().as_posix() in dir_array:
            tags.append(tag)
    return tags


def list_dirs(
    *,
    tag: str = 'default',
    show_all_tags: bool = False,
    list_one_per_line: bool = False,
) -> None:
    """List registered directories."""
    console = Console()
    config_file = tomlkit.toml_file.TOMLFile(CONFIG_FILE_PATH)
    doc = config_file.read()
    dir_table: tomlkit.items.Table = doc.get('directories', tomlkit.table())
    if list_one_per_line:
        dirs = set()
        for tag_, dir_array in dir_table.items():
            if not show_all_tags and tag_ != tag:
                continue
            dirs.update(dir_array)
        dirs = sorted(dirs)
        for dir_ in dirs:
            console.print(dir_)
        return
    for tag_, dir_array in dir_table.items():
        if not show_all_tags and tag_ != tag:
            continue
        console.print(f'{tag_}:')
        for i, dir_ in enumerate(dir_array):
            extra_tags = [
                t
                for t in get_tags(
                    dir_path=pathlib.Path(dir_), dir_table=dir_table
                )
                if t != tag_
            ]
            console.print(f'{i + 1}: {dir_} : {", ".join(extra_tags)}')


@main.command(
    name='list',
    help='List registered directories.',
)
@click.option(
    '-t',
    '--tag',
    'tag',
    type=str,
    default='default',
    show_default=True,
    help='tag of directories.',
)
@click.option(
    '-a',
    '--all',
    'show_all_tags',
    is_flag=True,
    help='List all directories of all tags.',
)
@click.option(
    '-1',
    'list_one_per_line',
    is_flag=True,
    help='List one directory per line.',
)
def list_dirs_command(
    *,
    tag: str = 'default',
    show_all_tags: bool = False,
    list_one_per_line: bool = False,
) -> None:
    """List registered directories."""
    list_dirs(
        tag=tag,
        show_all_tags=show_all_tags,
        list_one_per_line=list_one_per_line,
    )


if __name__ == '__main__':
    main()
