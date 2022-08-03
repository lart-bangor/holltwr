from typing import Iterable, Any
from pathlib import Path


class HolltwrError(Exception):
    ...


class JSONValidationError(HolltwrError):
    def __init__(
        self, *args: object,
        errors: Iterable[Any] | None = None
    ) -> None:
        self.errors = errors
        super().__init__(*args)


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
