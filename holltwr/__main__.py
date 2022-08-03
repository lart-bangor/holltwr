from pathlib import Path
from .conventions import Convention
from .parser import AnnotationParser
from .textgrids import TextGrid
from .utils import process_textgrid


def main():
    convention_file = Path("./conventions/lart5.json")
    convention = Convention.load(convention_file)
    parser = AnnotationParser(convention)
    result = parser.parse("achxpce-Truck passing")
    print(result.pretty())
    tgfile = Path(
        "./testdata/C101M_forAnalysis.syllables.TextGrid"
    )
    with TextGrid(tgfile) as tg:
        process_textgrid(tg, parser)
        tg.save(f"{tgfile.with_suffix('')}.processed.TextGrid")


if __name__ == "__main__":
    main()
