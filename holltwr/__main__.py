"""holltwr: The TextGrid Annotation Splitter.

**holltwr** (pronounced /ˈhɔɬ.tur/, Welsh for 'splitter') is a command line utility and
Python package for splitting compact Praat TextGrid annotations into several separate
tiers following a preset annotation convention.
"""
from .cli import main

if __name__ == "__main__":
    main()
