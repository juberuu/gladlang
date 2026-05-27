"""Type – runtime type objects (Number, String, List, Dict, etc.)."""

from gladlang.core.errors import RTError
from gladlang.values.primitives.number import Number
from gladlang.values.value import Value


class Type(Value):
    __slots__ = ("name", "pos_start", "pos_end", "context")

    def __init__(self, name):
        self.name = name
        self.pos_start = None
        self.pos_end = None
        self.context = None

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def is_true(self):
        return True

    def copy(self):
        return (
            Type(self.name)
            .set_context(self.context)
            .set_pos(self.pos_start, self.pos_end)
        )

    def get_comparison_is(self, other):
        return Number(1 if self is other else 0).set_context(self.context), None

    def get_comparison_eq(self, other, visited=None):
        if isinstance(other, Type):
            return Number(1 if self is other else 0).set_context(self.context), None

        return None, self._illegal(other)

    def get_comparison_instanceof(self, other):
        return None, RTError(
            self.pos_start,
            self.pos_end,
            "Right operand of INSTANCEOF must be a Class or Type",
            self.context,
        )

    def anded_by(self, other):
        return (
            Number(1 if (self.is_true() and other.is_true()) else 0).set_context(
                self.context
            ),
            None,
        )

    def ored_by(self, other):
        return (
            Number(1 if (self.is_true() or other.is_true()) else 0).set_context(
                self.context
            ),
            None,
        )

    def execute(self, args, interpreter=None):
        from gladlang.runtime.rt_result import RTResult

        return RTResult().failure(self._illegal())

    def get_attr(self, name_tok, context=None):
        return None, self._illegal()

    def set_attr(self, name_tok, value, context=None, visibility=None, as_final=False):
        return None, self._illegal()

    def get_element_at(self, index):
        return None, self._illegal()

    def set_element_at(self, index, value):
        return None, self._illegal()

    def notted(self):
        return None, self._illegal()

    def _illegal(self, other=None):
        if not other:
            other = self

        return RTError(self.pos_start, other.pos_end, "Illegal operation", self.context)

    def illegal_operation(self, other=None):
        return self._illegal(other)

    def __repr__(self):
        return f"<type {self.name}>"
