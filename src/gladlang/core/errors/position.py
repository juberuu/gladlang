"""Source position tracker – stores file, line, column, and index for error reporting."""


class Position:
    __slots__ = ("idx", "ln", "col", "fn", "ftxt")

    def __init__(self, idx, ln, col, fn, ftxt=None):
        self.idx = idx
        self.ln = ln
        self.col = col
        self.fn = fn
        self.ftxt = ftxt

    def detach_source(self):
        self.ftxt = None
        return self

    def advance(self, current_char=None):
        self.idx += 1
        self.col += 1

        if current_char == "\n":
            self.ln += 1
            self.col = 0

        return self

    def copy(self):
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)
