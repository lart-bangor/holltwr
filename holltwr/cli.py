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
    """holltwr: The TextGrid Annotation Splitter.

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


@main.command()
@click.argument(
    "source",
    type=click.Path(path_type=Path, exists=True, file_okay=True, dir_okay=False),
    nargs=-1,
    required=True
)
@click.option(
    "-d", "--destination",
    required=False,
    default=None,
    help=(
        "A path or renaming pattern for the output. "
        "If not specified files will be modified in-situ. "
        "An argument ending with a slash ('/' or '\\') will be treated as the "
        "path to a directory to store output files. "
        "An argument containing at most a single asterisk ('*') will be treated"
        " as a renaming pattern, where * will be replaced with the relative "
        "path and filename of the source file, except its final file extension."
    )
)
@click.option(
    "-c", "--convention",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, readable=True,
        resolve_path=True, path_type=Path
    ),
    default=None,
    help=(
        "Path to a compact annotation convention file. "
        "Can be left unspecified if a default convention has been set with the "
        f"command 'holltwr config default-convention'. "
        "The provided file must validate against holltwr's Convention JSON "
        f"Schema (see 'holltwr validate convention')."
    )
)
@click.option(
    '--yes', is_flag=True,
    help="Confirm that holltwr may overwrite files without prompting."
)
def split(
    source: tuple[Path],
    destination: str | None = None,
    convention: Path | None = None,
    yes: bool = False
):
    """Split a compact TextGrid tier according to an annotation convention.

    The split command will split a compact annotation tier in one or more
    TextGrid files (specified by SOURCE) following the a specified annotation
    convention, given either by the -c/--convention option or using a default
    convention which has been set globally for holltwr (via holltwr config
    default-convention).

    SOURCE can be either a single file name (e.g. myfile.TextGrid), a list of
    file names (e.g. first.TextGrid second.TextGrid), or a POSIX-compliant
    glob pattern, where '*' can be any string, '?' any single character, and
    '**' any directory including all of its subdirectories (e.g. *.TextGrid
    will target all the files with the .TextGrid extension in the current
    working directory).

    By default, holltwr will overwrite the files in-situ, i.e. if given
    myfile.TextGrid as SOURCE, it will modify that file.
    The option -d/--destination allows this behaviour to be modified, with
    holltwr instead writing the result to a different file. The destination
    can be a single file name (e.g. myupdatedfile.TextGrid), a path to a
    directory (e.g. updated_files/ -- directory paths must end in '/' or '\\'!),
    or a renaming pattern containing at most one '*' which will be replaced with
    the relative path and name of the input file minus its file extension (e.g.
    'holltwr split first.TextGrid second.TextGrid -d *_expanded.TextGrid' will
    write its output to the files first_expanded.TextGrid and
    second_expanded.TextGrid).

    Before holltwr modifies any files that already exist you will be prompted to
    confirm that you want to overwrite these files (this is because an
    annotation convention might include the instruction to remove the compact
    annotation tier, i.e. data could be lost). If you do not want to be prompted
    you can confirm that you are fine with this behaviour beforehand by
    specifying the option --yes.
    """
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
                + click.style("--convention", dim=True)
                + " or setting a default convention with the command "
                + click.style("holltwr ", fg="green")
                + click.style("config default-convention ", fg="cyan")
                + click.style("FILENAME", dim=True)
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
    if not yes:
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
    with click.progressbar(work_list) as progress:  # type: ignore
        progress: list[tuple[Path, Path]]
        for file in progress:
            _split_file(file[0], file[1])


@main.group()
def validate(**kwargs: dict[str, Any]):
    """Validate conventions and TextGrids."""
    pass

@validate.command()
@click.argument(
    "filename",
    type=click.Path(
        path_type=Path, exists=True,
        file_okay=True, dir_okay=False,
        readable=True
    ),
    required=True
)
def convention(filename: Path):
    """Validate a compact annotation convention.

    Checks that a compact annotation convention conforms to holltwr's JSON
    Schema and can be loaded by holltwr, giving feedback if any errors or
    issues are found.
    """
    _validate_convention(filename)


@validate.command()
@click.argument(
    "filename",
    type=click.Path(
        path_type=Path, exists=True,
        file_okay=True, dir_okay=False,
        readable=True
    ),
    required=True
)
def textgrid(filename: Path):
    """Validate a TextGrid file."""
    click.secho("ERROR: ", fg="red", nl=False)
    click.echo("This functionality has not been implemented yet.")


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


def _split_file(source: Path | str, dest: Path | str):
    convention_file = Path("./conventions/lart5.json")
    convention = Convention.load(convention_file)
    parser = AnnotationParser(convention)
    with TextGrid(str(source)) as tg:
        process_textgrid(tg, parser)
        tg.save(str(dest))
