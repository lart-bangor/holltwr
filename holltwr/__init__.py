"""holltwr: The TextGrid Annotation Splitter.

**holltwr** (pronounced /ˈhɔɬ.tur/, Welsh for 'splitter') is a command line utility and
Python package for splitting compact Praat TextGrid annotations into several separate
tiers following a preset annotation convention.
"""
from .conventions import Convention
from .parser import AnnotationParser

__all__ = ["Convention", "AnnotationParser"]
