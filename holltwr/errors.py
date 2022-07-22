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
