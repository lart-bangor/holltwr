"""High-level utility functions implementing holltwr functionality."""
from .conventions import Convention
from .parser import AnnotationParser
from .textgrids import TextGrid
from .errors import TextGridError


def check_compact_tier(tg: TextGrid, name: str) -> None:
    """Check that a TextGrid has the named named IntervalTier or raise an exception."""
    if not tg.hastier(name):
        raise TextGridError(f"Missing compact tier {name!r}", tg.path)
    if not tg.hasintervaltier(name):
        raise TextGridError(f"Compact tier {name!r} is not an IntervalTier", tg.path)


def prepare_textgrid(
    tg: TextGrid, convention: Convention,
    *, allow_override: bool = False
) -> None:
    """Add the specified tiers to the TextGrid.

    Raises a TextGridError if any of the tiers exist already and `allow_override`
    is `False`.
    """
    check_compact_tier(tg, convention.options.compact_tier)
    for tier_name in convention.tiers:
        if tg.hastier(tier_name):
            if allow_override:
                tg.removetier(tier_name)
            else:
                raise TextGridError(
                    f"A tier with the name {tier_name!r} already exists"
                )
    compact_tier = convention.options.compact_tier
    for tier_name in convention.tiers:
        tg.duplicatetier(compact_tier, tier_name, markers=True, labels=False)


def process_textgrid(
    tg: TextGrid, parser: AnnotationParser,
    *, allow_override: bool = False
):
    """Process a TextGrid using an AnnotationParser."""
    prepare_textgrid(tg, parser.convention, allow_override=allow_override)
    # Parse and add annotations
    target_tiers = {name: tg.gettier(name) for name in parser.convention.tiers}
    for compact_entry in tg.itertier(parser.convention.options.compact_tier):
        parse = parser.parse(compact_entry.label)  # type: ignore
        for parsed_tier_name, parsed_entry in parse.tiers.items():
            target_tiers[parsed_tier_name].insertEntry(  # type: ignore
                TextGrid.update_interval(
                    compact_entry,  # type: ignore
                    label=parsed_entry.join()
                ),
                collisionMode="replace",
                collisionReportingMode="silence"
            )
