"""Enum – represents enumeration types with case name -> value mapping."""

from gladlang.core.errors import RTError
from gladlang.values.primitives.number import Number
from gladlang.values.value import Value


class Enum(Value):
    __slots__ = ("name", "elements_dict", "pos_start", "pos_end", "context")

    def __init__(self, name, elements_dict):
        self.name = name
        self.elements_dict = elements_dict
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

    def get_attr(self, name_tok, context=None):
        name = name_tok.value
        if name in self.elements_dict:
            val = self.elements_dict[name]
            return val.copy().set_pos(name_tok.pos_start, name_tok.pos_end), None

        return None, RTError(
            name_tok.pos_start,
            name_tok.pos_end,
            f"Enum '{self.name}' has no case '{name}'",
            self.context,
        )

    def set_attr(self, name_tok, value, context=None, visibility=None, as_final=False):
        return None, RTError(
            name_tok.pos_start,
            name_tok.pos_end,
            f"Cannot reassign enum case '{name_tok.value}'",
            self.context,
        )

    def get_comparison_eq(self, other, visited=None):
        if isinstance(other, Enum):
            return Number(1 if self is other else 0).set_context(self.context), None

        return None, self._illegal(other)

    def get_comparison_ne(self, other):
        if isinstance(other, Enum):
            return Number(1 if self is not other else 0).set_context(self.context), None

        return None, self._illegal(other)

    def get_comparison_is(self, other):
        return Number(1 if self is other else 0).set_context(self.context), None

    def get_comparison_instanceof(self, other):
        from gladlang.values.classes.type_ import Type
        from gladlang.values.classes.class_ import Class

        if isinstance(other, Type):
            if other.name == "Enum":
                return Number.true.copy(), None

            if other.name == "Object":
                return Number.true.copy(), None

            return Number.false.copy(), None

        if isinstance(other, Class):
            return Number.false.copy(), None

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

    def execute(self, args, interpreter=None, calling_context=None):
        from gladlang.runtime.rt_result import RTResult

        return RTResult().failure(self._illegal())

    def notted(self):
        return None, self._illegal()

    def copy(self):
        c = Enum(self.name, self.elements_dict)
        c.set_pos(self.pos_start, self.pos_end)
        c.set_context(self.context)
        return c

    def _illegal(self, other=None):
        if not other:
            other = self

        return RTError(self.pos_start, other.pos_end, "Illegal operation", self.context)

    def illegal_operation(self, other=None):
        return self._illegal(other)

    def __repr__(self):
        return f"<enum {self.name}>"
