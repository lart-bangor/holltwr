"""Compact TextGrid Annotation Conventions

This module provides functionality for loading, storing, and using *holltwr*'s TextGrid
Annotation Conventions.
"""
import importlib.resources
import json
import jschon
from collections import ChainMap
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TextIO, TypeGuard, Any
from typing_extensions import Self
from .errors import JSONValidationError


def _is_str(x: Any) -> TypeGuard[str]:
    return isinstance(x, str)


_json_catalog = jschon.create_catalog("2020-12")
_json_schema: jschon.JSONSchema | None = None


def _get_schema() -> jschon.JSONSchema:
    global _json_schema
    return _json_schema or (
        _json_schema := jschon.JSONSchema.loads(  # type: ignore
            importlib.resources.read_text(__package__, "convention.schema.json")
        )
    )


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

    Functions: tuple[str, str] = ("part-separator", "comment")
    FunctionT = Literal["part-separator", "comment"]

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
            raise TypeError(
                f"SpecialTag function must be one of {self.Functions}, {type(function)} given"
            )
        self._function = function

    @property
    def preserve(self) -> bool:
        return self._preserve

    @preserve.setter
    def preserve(self, preserve: bool):
        self._preserve = bool(preserve)

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}({self.input!r}, "
                f"{self.function!r}, {self.output!r}, {self.preserve!r})")

    def __str__(self) -> str:
        if not self.preserve:
            return f"{self.__class__.__name__}({self.function}: {self.input} -> None)"
        return f"{self.__class__.__name__}({self.function}: {self.input} -> {self.output}...)"


@dataclass
class Meta:
    name: str
    version: str
    date: str
    description: str = ""
    author: str = ""

    @classmethod
    def fromdata(cls, data: dict[str, str]) -> Self:
        return cls(**data)

    def todata(self) -> dict[str, str]:
        return {
            "name": self.name,
            "version": self.version,
            "date": self.date,
            "description": self.description,
            "author": self.author
        }


@dataclass
class Options:
    compact_tier: str
    retain_compact: bool = True
    case_sensitive: bool = True
    tag_separator: str = ","

    @classmethod
    def fromdata(cls, data: dict[str, str | bool]) -> Self:
        keys = list(data.keys())
        for key in keys:
            data[key.replace("-", "_")] = data.pop(key)
        return cls(**data)  # type: ignore

    def todata(self) -> dict[str, str | bool]:
        d: dict[str, str | bool] = {"compact-dir": self.compact_tier}
        if not self.retain_compact:
            d["retain-compact"] = False
        if not self.case_sensitive:
            d["case-sensitive"] = False
        if self.tag_separator != ",":
            d["tag-separator"] = self.tag_separator
        return d


@dataclass
class Tier:
    name: str
    content: dict[str, Tag | SpecialTag]

    @classmethod
    def fromdata(cls, data: tuple[str, list[str]], tagrefs: dict[str, Tag | SpecialTag]) -> Self:
        name = data[0]
        content: dict[str, Tag] = {}
        for tag in data[1]:
            if tag not in tagrefs:
                raise ValueError(f"No tag reference found for tag {tag!r}")
            content[tag] = tagrefs[tag]
        return cls(name, content)

    def todata(self) -> tuple[str, list[str]]:
        return (self.name, list(self.content.keys()))


class Convention:

    meta: Meta
    options: Options
    special_tags: dict[str, SpecialTag]
    tags: dict[str, Tag]
    tiers: dict[str, Tier]
    alltags: ChainMap[str, Tag | SpecialTag]

    def __init__(
        self,
        meta: Meta,
        options: Options,
        special_tags: dict[str, SpecialTag],
        tags: dict[str, Tag],
        tiers: dict[str, Tier]
    ):
        self.meta = meta
        self.options = options
        self.special_tags = special_tags
        self.tags = tags
        self.tiers = tiers
        self.alltags = ChainMap(self.tags, self.special_tags)   # type: ignore

    @classmethod
    def fromdata(cls, data: dict[str, dict[str, Any]]) -> Self:
        testdata = jschon.JSON(data)
        schema = _get_schema()
        result = schema.evaluate(testdata)
        cls._raise_validation_status(result)
        meta = Meta.fromdata(data["meta"])
        options = Options.fromdata(data["options"])
        special_tags: dict[str, SpecialTag] = {}
        for tag_label, tag_props in data["special-tags"].items():
            special_tags[tag_label] = SpecialTag(tag_label, **tag_props)
        tags:  dict[str, Tag] = {}
        for tag_label, tag_props in data["tags"].items():
            tags[tag_label] = Tag(tag_label, *tag_props)
        alltags: ChainMap[str, Tag | SpecialTag] = ChainMap(tags, special_tags)  # type: ignore
        tiers: dict[str, Tier] = {}
        for tier_label, tier_tag_labels in data["tiers"].items():
            tier_tags: dict[str, Tag | SpecialTag] = {}
            for tag_label in tier_tag_labels:
                if tag_label not in alltags:
                    raise KeyError(f"Tier {tier_label!r} references undefined tag {tag_label!r}")
                tier_tags[tag_label] = alltags[tag_label]
            tiers[tier_label] = Tier(tier_label, tier_tags)
        return cls(meta=meta, options=options, special_tags=special_tags, tags=tags, tiers=tiers)

    @classmethod
    def _raise_validation_status(cls, result: jschon.jsonschema.Scope):
        if not result.valid:
            raise JSONValidationError(
                "Convention data failed validation",
                errors=list(result.collect_errors())  # type: ignore
            )

    @classmethod
    def load(cls, file: Path | str | TextIO) -> Self:
        if isinstance(file, str):
            file = Path(file)
        if isinstance(file, Path):
            with file.open("r") as fp:
                return cls.fromdata(json.load(fp))
        return cls.fromdata(json.load(file))

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}({self.meta!r}, {self.options!r}, "
            f"{self.special_tags!r}, {self.tags!r}, {self.tiers!r})"
        )

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}({self.meta.name!r}, v{self.meta.version})"
        )
