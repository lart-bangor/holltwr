"""Compact TextGrid Annotation Conventions.

This module provides functionality for loading, storing, and using *holltwr*'s TextGrid
Annotation Conventions.
"""
from typing import Literal, TypeGuard, Any
from typing_extensions import Self


def _is_str(x: Any) -> TypeGuard[str]:
    return isinstance(x, str)


class Tag:

    _input: str
    _output: str
    description: str

    def __init__(self, input: str, output: str, description: str | None = None):
        self.input = input
        self.output = output
        self.description = description or ""

    @classmethod
    def fromdata(cls, data: tuple[str, list[str]]) -> Self:
        return cls(data[0], *data[1])

    def todata(self) -> tuple[str, list[str]]:
        return (self.input, [self.output, self.description])

    @property
    def input(self) -> str:
        return self._input

    @input.setter
    def input(self, input: str):
        if not _is_str(input):
            raise TypeError(f"Tag input must be of type 'str', {type(input)} given")
        if not len(input) == 1:
            raise ValueError(f"Tag input must be exactly 1 character, {len(input)} given")
        self._input = input

    @property
    def output(self) -> str:
        return self._output

    @output.setter
    def output(self, output: str):
        if not _is_str(output):
            raise TypeError(f"Tag input must be of type 'str', {type(input)} given")
        self._output = output

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.input!r}, {self.output!r}, {self.description!r})"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.input} -> {self.output})"


class SpecialTag(Tag):

    Functions: tuple[str, str] = ("overlap-separator", "comment")
    FunctionT = Literal["overlap-separator", "comment"]

    _function: FunctionT
    _preserve: bool

    def __init__(
        self, input: str, function: FunctionT, output: str = "", preserve: bool = False
    ):
        super().__init__(input, output, function)
        self.function = function
        self.preserve = preserve

    @classmethod
    def fromdata(cls, data: tuple[str, dict[str, str | bool]]) -> Self:  # type: ignore
        if "function" not in data[1]:
            raise ValueError("SpecialTag must have 'function' specified.")
        function = data[1].pop("function")
        return cls(data[0], function, **data[1])  # type: ignore

    def todata(self) -> tuple[str, dict[str, str | bool]]:  # type: ignore
        d: dict[str, str | bool] = {"function": self.function}
        if self.output:
            d["output"] = self.output
        if self.preserve:
            d["preserve"] = self.preserve
        return (self.input, d)

    @property
    def function(self) -> FunctionT:
        return self._function

    @function.setter
    def function(self, function: FunctionT):
        if function not in self.Functions:
            raise TypeError(f"SpecialTag function must be one of {self.Functions}, {type(function)} given")
        self._function = function

    @property
    def preserve(self) -> bool:
        return self._preserve

    @preserve.setter
    def preserve(self, preserve: bool):
        self._preserve = bool(preserve)

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}({self.input!r}, "
                f"{self.function!r}, {self.output!r}, , {self.preserve!r})")

    def __str__(self) -> str:
        if not self.preserve:
            return f"{self.__class__.__name__}({self.function}: {self.input} -> None)"
        return f"{self.__class__.__name__}({self.function}: {self.input} -> {self.output}...)"


class Meta:
    ...


class Convention:

    name: str

    def __init__(self):
        ...
