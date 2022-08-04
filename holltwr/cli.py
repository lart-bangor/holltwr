"""The Command Line Interface (CLI) of holltwr."""
from __future__ import annotations
import click
import json
from appdirs import AppDirs
from pathlib import Path
from typing import Any, ClassVar
from sys import exit

from .errors import JSONValidationError, ExitCode
from .conventions import Convention
from .parser import AnnotationParser
from .textgrids import TextGrid
from .utils import process_textgrid


dirs = AppDirs(
    appname="holltwr",
    appauthor="LART",
    roaming=True
)

JSONableKeyType = str | int | float | None
JSONableType = (
    JSONableKeyType
    | bool
    | dict[JSONableKeyType, "JSONableType"]
    | list["JSONableType"]
    | tuple["JSONableType"]
)


class Configuration:
    __reserved: ClassVar = (
        "__init__", "__getattr__", "__setattr__",
        "_path", "_config", "_repair",
        "load", "reset", "save"
    )
    _path: Path
    _config: dict[JSONableKeyType, JSONableType]

    def __init__(self, config_dir: Path | None = None):
        global dirs
        if not config_dir:
            self._path = Path(dirs.user_config_dir) / "holltwr-config.json"
        if not self._path.exists():
            self._repair()
        self.load()

    def load(self):
        with self._path.open("r") as fp:
            try:
                self._config = json.load(fp)
            except json.JSONDecodeError as e:
                print(f"Error reading configuration file: {e}")
                print("Resetting configuration file...")
                self._repair()
        if not isinstance(self._config, dict):
            self.reset()

    def reset(self):
        self._config = {}

    def _repair(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)
        self.reset()
        self.save()

    def save(self):
        with self._path.open("w") as fp:
            json.dump(self._config, fp)

    def __getattr__(self, name: str) -> JSONableType:
        if name in self._config:
            return self._config[name]
        raise AttributeError(f"The configuration has no attribute {name!r}")

    def __setattr__(self, name: str, value: JSONableType) -> None:
        if name in self.__reserved:
            return super().__setattr__(name, value)
        if name.startswith("_"):
            raise AttributeError(f"The configuration has no attribute {name!r}")
        self._config[name] = value


configuration = Configuration()


@click.group()
def main(**kwargs: dict[str, Any]):
    """A command line utility for splitting compact Praat TextGrid annotations.

    holltwr /ˈhɔɬ.tur/ is a command line utility for automated splitting of
    compact Praat TextGrid annotations into several separate tiers following
    a set annotation and conversion convention.

    For instance, holltwr can take a TextGrid that only has a compact "manual"
    tier with an annotation such as "rexpcu-Researcher coughing" and split this
    across several tiers, e.g. a speaker tier showing "Researcher/Participant",
    a language tier showing "English/Welsh,Unknown" and comment tier showing
    "Researcher coughing". This can greatly speed up the work required to
    annotate an audio recording for basic categorial interval factors.
    """
    pass


def _split_file(source, dest):
    convention_file = Path("./conventions/lart5.json")
    convention = Convention.load(convention_file)
    parser = AnnotationParser(convention)
    with TextGrid(str(source)) as tg:
        process_textgrid(tg, parser)
        tg.save(str(dest))


@main.command()
@click.argument(
    "source",
    type=click.Path(path_type=Path, exists=True, file_okay=True, dir_okay=False),
    nargs=-1
)
@click.option(
    "-d", "--destination",
    required=False,
    default=None
)
@click.option(
    "-c", "--convention",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, readable=True,
        resolve_path=True, path_type=Path
    ),
    default=None
)
def split(source: tuple[Path], destination: str | None = None, convention: Path | None = None):
    global configuration
    if convention is None:
        if hasattr(configuration, "default_convention"):
            convention = Path(getattr(configuration, "default_convention"))
        else:
            click.secho("ERROR: ", fg="red", nl=False)
            click.echo(
                "No convention file was specified and no default convention"
                " file has been configured."
            )
            click.echo(
                "Have you tried to specify a convention file with the option "
                + click.style("--convention", fg="black")
                + " or setting a default convention with the command "
                + click.style("holltwr ", fg="green")
                + click.style("config default-convention ", fg="white")
                + click.style("FILENAME", fg="black")
                + "?"
            )
            exit(ExitCode.GENERAL_ERROR)
    if len(source) == 0:
        click.secho("ERROR: ", fg="red", nl=False)
        click.echo("No files matching the pattern for the SOURCE argument found.")
        exit(ExitCode.FILE_NOT_FOUND)
    if destination and destination.count("*") > 1:
        click.secho("ERROR: ", fg="red", nl=False)
        click.echo("The argument DESTINATION can at most contain one wildcard '*'.")
        exit(ExitCode.GENERAL_ERROR)
    if destination and "*" in destination and ("\\" in destination or "/" in destination):
        click.secho("ERROR: ", fg="red", nl=False)
        click.echo("Wildcard patterns for DESTINATION must not contain directory paths.")
        exit(ExitCode.GENERAL_ERROR)
    work_list: list[tuple[Path, Path]] = []
    destfiles: set[Path] = set()
    for infile in source:
        if not destination:
            destfile = infile
        elif "*" in destination:
            destfile = infile.parent / destination.replace("*", infile.stem)
        elif destination.endswith("/") or destination.endswith("\\"):
            destfile = Path(destination) / infile.resolve().relative_to(Path.cwd())
        else:
            destfile = Path(destination)
        if destfile in destfiles:
            print(destfile, "IN", destfiles)
            click.secho("ERROR: ", fg="red", nl=False)
            click.echo("DESTINATION path is identical for several files.")
            click.echo(
                "Try using a wildcard '*' or giving a directory path ending in '/' as DESTINATION?"
            )
            exit(ExitCode.GENERAL_ERROR)
        destfiles.add(destfile)
        work_list.append((infile, destfile))
    # Check if any of the target files already exist
    dest_exists: set[Path] = set()
    for destfile in destfiles:
        if destfile.exists():
            dest_exists.add(destfile)
    if dest_exists:
        click.secho("ATTENTION: ", fg="red", nl=False)
        click.echo("The following file(s) already exist and will be overwritten:")
        counter = 1
        for destfile in dest_exists:
            click.secho(f"[{counter}] ", fg="red", nl=False)
            click.secho(str(destfile), fg="blue")
        if not click.confirm("Do you wish to proceed?"):
            exit(ExitCode.GENERAL_ERROR)
    with click.progressbar(work_list) as progress:
        for file in progress:
            _split_file(file[0], file[1])


@main.group()
def config(**kwargs: dict[str, Any]):
    """Configure global settings for holltwr.

    Use these commands to set the global configuration for holltwr, such as
    a default convention to use if not otherwise specified.
    """
    pass

@config.command()
@click.confirmation_option(
    prompt="Are you sure you want to reset all of custom configuration settings?"
)
def reset():
    """Reset/remove all custom configuration for holltwr."""
    global configuration
    configuration.reset()
    configuration.save()

@config.command()
@click.argument(
    "filename",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, readable=True,
        resolve_path=True, path_type=Path
    )
)
def default_convention(filename: Path):
    """Set the default convention to be used.

    This will set FILENAME as the default convention file to be used with
    holltwr if whenever a more specific convention file is not specified via
    the command line option -c/--convention.
    """
    global configuration
    _validate_convention(filename)
    click.secho("Updating default convention file ... ", fg="yellow", nl=False)
    configuration.default_convention = str(filename)
    configuration.save()
    click.secho("OK.", bold=True)


# @main.command()
# @click.argument(
#     "filename",
#     type=click.Path(
#         exists=True, file_okay=True, dir_okay=False, readable=True,
#         resolve_path=True, path_type=Path
#     )
# )
def _validate_convention(filename: Path) -> Convention:
    """Validate a convention file."""
    click.secho("Validating convention file ", fg="yellow", nl=False)
    click.secho(str(filename), fg="blue", nl=False)
    click.secho(" ... ", fg="yellow", nl=False)
    try:
        convention = Convention.load(filename)
        click.secho("OK.", bold=True)
        return convention
    except JSONValidationError as e:
        click.secho("\nERROR: ", fg="red", nl=False)
        click.echo(e)
        counter = 1
        for error in e.errors:
            click.secho(f"[{counter}] ", fg="red", dim=True, nl=False)
            click.secho(f"{error[0]}: ", fg="blue", dim=True, nl=False),
            click.secho(error[1], dim=True)
        exit(ExitCode.JSON_VALIDATION_ERROR)
    except Exception as e:
        click.secho("\nERROR: ", fg="red", nl=False)
        click.echo(e)
        exit(ExitCode.JSON_IO_ERROR)