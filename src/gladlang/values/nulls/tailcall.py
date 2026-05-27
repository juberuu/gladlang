"""TailCall – marker for tail call optimisation (TCO) in recursive functions."""


class TailCall:
    __slots__ = ("function", "args")

    def __init__(self, function, args):
        self.function = function
        self.args = args
