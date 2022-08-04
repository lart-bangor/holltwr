from pathlib import Path
from jschon.json import JSONCompatible
import enum


@enum.unique
class ExitCode(enum.IntFlag):
    OK = 0
    GENERAL_ERROR = 1
    CONFIGURATION_ERROR = 2
    FILE_NOT_FOUND = 4
    FILE_IO_ERROR = 8
    JSON_IO_ERROR = 16
    JSON_VALIDATION_ERROR = 32


class HolltwrError(Exception):
    ...


class JSONValidationError(HolltwrError):
    def __init__(
        self, *args: object,
        errors: JSONCompatible | None = None
    ) -> None:
        self.errors = self.collect_errors(errors)
        super().__init__(*args)

    @staticmethod
    def collect_errors(errors: JSONCompatible) -> list[tuple[str, str]]:
        if not isinstance(errors, dict):
            return list()
        error_list: list[tuple[str, str]] = list()
        if "error" in errors:
            error_list.append((errors["keywordLocation"], errors["error"]))
        if "errors" in errors and isinstance(errors["errors"], list):
            for suberror in errors["errors"]:
                suberror: JSONCompatible
                suberror_list = JSONValidationError.collect_errors(suberror)
                error_list.extend(suberror_list)
        return error_list


class ParsingError(HolltwrError):
    ...


class UnknownTagError(HolltwrError):
    def __init__(
        self,
        msg: str | None = None,
        tag: str | None = None,
        file: str | Path | None = None
    ):
        self.tag = tag
        self.file = file
        if not msg:
            msg = "Parser encountered unknown tag"
            if tag:
                msg += f" {tag!r}"
        if file:
            msg += f" in file {file}"
        super().__init__(msg)


class TextGridError(HolltwrError):
    def __init__(
        self,
        msg: str | None = None,
        file: str | Path | None = None
    ):
        self.file = file
        if msg and file:
            msg += f" in file {file}"
        super().__init__(msg)
