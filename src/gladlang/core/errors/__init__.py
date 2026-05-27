"""Error handling package – exposes position, error types, and runtime error classes."""

from .position import Position
from .error import Error
from .illegal_char_error import IllegalCharError
from .invalid_syntax_error import InvalidSyntaxError
from .rt_error import RTError

__all__ = ["Position", "Error", "IllegalCharError", "InvalidSyntaxError", "RTError"]
