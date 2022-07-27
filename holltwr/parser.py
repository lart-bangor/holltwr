"""Compact TextGrid Annotation Parsing"""
import enum
from typing import NamedTuple, NewType

from holltwr.errors import UnknownTagError
from . import conventions


class AnnotationTierType(enum.Enum):
    GENERAL = enum.auto()
    COMMENT = enum.auto()


class AnnotationPart(NamedTuple):
    compact: str
    separator: str
    expanded: tuple[str]

    def join(self) -> str:
        return self.separator.join(self.expanded)

    __str__ = join


class AnnotationTier(NamedTuple):
    separator: str
    parts: tuple[AnnotationPart]
    type: AnnotationTierType = AnnotationTierType.GENERAL

    @property
    def compact(self) -> str:
        return "".join(set("".join(part.compact for part in self.parts)))

    def join(self) -> str:
        return self.separator.join(part.join() for part in self.parts)

    __str__ = join


AnnotationTierMap = NewType("AnnotationTierMap", dict[str, AnnotationTier])


class AnnotationParse(NamedTuple):
    convention: conventions.Convention
    compact: str
    tiers: AnnotationTierMap

    def joined(self) -> dict[str, str]:
        return {name: tier.join() for name, tier in self.tiers.items()}

    def __str__(self) -> str:
        return str(self.joined())

    def pretty(self) -> str:
        out = f"{self.__class__.__name__}(\n"
        out += f"  {self.convention.options.compact_tier}: '{self.compact}'\n"
        out += "\n".join(f"  {name}: '{tier}'" for name, tier in self.tiers.items())
        out += "\n)"
        return out


class AnnotationParser:
    _convention: conventions.Convention
    _comment_marker: conventions.SpecialTag
    _part_separator: conventions.SpecialTag

    def __init__(self, convention: conventions.Convention, filename: str | None = None):
        self.convention = convention
        self.filename = filename

    @property
    def convention(self) -> conventions.Convention:
        return self._convention

    @convention.setter
    def convention(self, convention: conventions.Convention):
        self._convention = convention
        for special_tag in convention.special_tags.values():
            if special_tag.function == "comment":
                self._comment_marker = special_tag
            if special_tag.function == "part-separator":
                self._part_separator = special_tag

    def parse(self, compact: str) -> AnnotationParse:
        remainder = compact
        comment: str | None = None
        if self._comment_marker.input in remainder:
            remainder, comment = remainder.split(self._comment_marker.input, 1)
        compact_parts: list[str] = remainder.split(self._part_separator.input)
        base_parts = {part: self.parse_part(part) for part in compact_parts}
        tiers = self.make_tiers(base_parts, comment)
        return AnnotationParse(self.convention, compact, tiers)

    def parse_part(self, compact_part: str) -> list[str]:
        etags: list[str] = []
        for ctag in compact_part:
            if ctag not in self._convention.tags:
                raise UnknownTagError(tag=ctag, file=self.filename)
            etags.append(self._convention.tags[ctag].output)
        return etags

    def make_tiers(
        self,
        base_parts: dict[str, list[str]],
        comment: str | None
    ) -> AnnotationTierMap:
        tier_map: dict[str, AnnotationTier] = {}
        for tname, tprops in self.convention.tiers.items():
            if self.is_pure_comment_tier(tprops):
                tier_map[tname] = self.make_comment_tier(comment)
            else:
                tier_map[tname] = self.make_general_tier(tprops, base_parts, comment)
        return AnnotationTierMap(tier_map)

    def is_pure_comment_tier(self, tier: conventions.Tier) -> bool:
        """Determine whether a tier convention encodes a pure comment tier."""
        return len(tier.content) == 1 and tuple(tier.content) == (self._comment_marker.input,)

    def make_comment_tier(self, comment: str | None = None) -> AnnotationTier:
        """Make a one-part AnnotationTier of type `AnnotationTierType.COMMENT`."""
        return AnnotationTier(
                    self._part_separator.output,
                    (AnnotationPart(
                        str(comment),
                        self.convention.options.tag_separator,
                        (self.make_comment_str(comment),)
                    ),),
                    type=AnnotationTierType.COMMENT
                )

    def make_comment_str(self, comment: str | None = None) -> str:
        """Prepare a string with representation with comment marker from a comment."""
        return self._comment_marker.output + (comment or "")

    def make_general_tier(
        self,
        tier: conventions.Tier,
        base_parts: dict[str, list[str]],
        comment: str | None
    ) -> AnnotationTier:
        """Make a multi-part general AnnotationTier"""
        parts: list[AnnotationPart] = []
        for base_part in base_parts:
            compact_part: list[str] = []
            expanded_part: list[str] = []
            for ctag in tier.content:
                if ctag in base_part:
                    compact_part.append(ctag)
                    expanded_part.append(tier.content[ctag].output)
                if ctag == self._comment_marker.input:
                    compact_part.append(self._comment_marker.input)
                    expanded_part.append(self.make_comment_str(comment))
            parts.append(AnnotationPart(
                "".join(compact_part),
                self.convention.options.tag_separator,
                tuple(expanded_part)
            ))
        return AnnotationTier(
            self._part_separator.output,
            tuple(parts)
        )
