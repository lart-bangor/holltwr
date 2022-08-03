"""Module for reading, writing and processing TextGrid files with holltwr."""
from pathlib import Path
from types import TracebackType
from typing import Any, Iterator, Type
from typing_extensions import Self
from praatio.textgrid import Textgrid, openTextgrid          # type: ignore
from praatio.data_classes.textgrid_tier import TextgridTier  # type: ignore
from praatio.utilities.constants import Interval, Point      # type: ignore
from .errors import TextGridError

__all__ = ["TextGrid"]


class TextGrid():
    """A simpler interface to the praatio.textgrid API tailored to holltwr's needs."""

    tg: Textgrid
    path: Path

    def __init__(self, file: Path | str):
        self.path = file.resolve() if isinstance(file, Path) else Path(file).resolve()
        self.tg = openTextgrid(str(self.path), True, "warning", "error")

    def hastier(self, name: str) -> bool:
        return name in self.tg.tierNameList

    def hasintervaltier(self, name: str) -> bool:
        return name in self.tg.tierNameList and self.tg.tierDict[name].tierType == "IntervalTier"

    def haspointtier(self, name: str) -> bool:
        return name in self.tg.tierNameList and self.tg.tierDict[name].tierType == "TextTier"

    def removetier(self, name: str) -> Self:
        self.tg.removeTier(name)
        return self

    def duplicatetier(
        self, src_name: str, new_name: str,
        *, markers: bool = True, labels: bool = True
    ) -> Self:
        if src_name not in self.tg.tierNameList:
            raise TextGridError(f"No tier named '{src_name!r}'", self.path)
        if new_name in self.tg.tierNameList:
            raise TextGridError(f"Tier named {new_name!r} already exists", self.path)
        new_entries: None | list[None] = None if markers else []
        new_tier = self.tg.tierDict[src_name].new(  # type: ignore
            name=new_name, entryList=new_entries
        )
        if markers and not labels:
            entryT = new_tier.entryType
            if entryT == Point:
                relabel_entry = self.update_point
            else:
                relabel_entry = self.update_interval
            for entry in new_tier.entryList:  # type: ignore
                entry: Point | Interval
                new_tier.insertEntry(  # type: ignore
                    relabel_entry(entry, label=""),  # type: ignore
                    collisionMode="replace",
                    collisionReportingMode="silence"
                )

        self.tg.addTier(new_tier)
        return self

    def itertier(self, name: str) -> Iterator[Point | Interval]:
        if name not in self.tg.tierNameList:
            raise TextGridError(f"No tier named '{name!r}'", self.path)
        return iter(self.tg.tierDict[name].entryList)  # type: ignore

    def gettier(self, name: str) -> TextgridTier:
        if name not in self.tg.tierNameList:
            raise TextGridError(f"No tier named '{name!r}'", self.path)
        return self.tg.tierDict[name]

    def getentries(self, tier_name: str) -> list[Point] | list[Interval]:
        return self.gettier(tier_name).entryList  # type: ignore

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None
    ) -> bool | None:
        return None

    def save(self, path: Path | str | None = None) -> Self:
        if path is None:
            path = self.path
        else:
            path = path.resolve() if isinstance(path, Path) else Path(path).resolve()
        self.tg.save(str(path), format="long_textgrid", includeBlankSpaces=True)
        self.path = path
        return self

    def todata(self) -> dict[str, Any]:
        return {
            "tierNameList": self.tg.tierNameList,
            "tierDict": {
                name: {
                    "tierType": tier.tierType,
                    "entryType": tier.entryType,
                    "entryList": tier.entryList,  # type: ignore
                    "minTimestamp": tier.minTimestamp,
                    "maxTimestamp": tier.maxTimestamp
                } for name, tier in self.tg.tierDict.items()
            },
            "minTimestamp": self.tg.minTimestamp,
            "maxTimestamp": self.tg.maxTimestamp
        }

    @staticmethod
    def update_point(original: Point, time: Any = ..., label: Any = ...) -> Point:
        if time is ...:
            time = original.time  # type: ignore
        if label is ...:
            label = original.label  # type: ignore
        return Point(time, label)

    @staticmethod
    def update_interval(
        original: Interval, start: Any = ..., end: Any = ..., label: Any = ...
    ) -> Interval:
        if start is ...:
            start = original.start  # type: ignore
        if end is ...:
            end = original.end  # type: ignore
        if label is ...:
            label = original.label  # type: ignore
        return Interval(start, end, label)
