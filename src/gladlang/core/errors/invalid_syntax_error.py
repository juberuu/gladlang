"""Invalid syntax error – raised when the parser detects a grammar violation."""

from .error import Error


class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details=""):
        super().__init__(pos_start, pos_end, "Invalid Syntax", details)
