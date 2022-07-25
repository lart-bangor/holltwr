from typing import Iterable, Any


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
        file: str | None = None
    ):
        self.tag = tag
        if not msg:
            msg = "Parser encountered unknown tag"
            if tag:
                msg += f" {tag!r}"
            if file:
                msg += f" in file {file}"
        super().__init__(msg)
