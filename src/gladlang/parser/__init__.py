"""Parser package – exposes ParseResult and Parser classes."""

from .parse_result import ParseResult
from .parser import Parser
from .ast import *

__all__ = ["ParseResult", "Parser"]
