"""String – immutable character sequence with concatenation, repetition, and indexing."""

from gladlang.core.errors import RTError
from gladlang.values.primitives.number import Number
from gladlang.values.value import Value


class String(Value):
    MAX_STRING_SIZE = 10_000_000

    __slots__ = ("value", "pos_start", "pos_end", "context")

    def __init__(self, value):
        self.value = value
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

    def added_to(self, other):
        if isinstance(other, String):
            new_len = len(self.value) + len(other.value)
            if new_len > String.MAX_STRING_SIZE:
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    f"String concatenation result ({new_len:,} chars) exceeds maximum allowed size ({String.MAX_STRING_SIZE:,} chars)",
                    self.context,
                )

            return String(self.value + other.value).set_context(self.context), None

        elif isinstance(other, Number):
            suffix = str(other.value)
            new_len = len(self.value) + len(suffix)
            if new_len > String.MAX_STRING_SIZE:
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    f"String concatenation result exceeds maximum allowed size ({String.MAX_STRING_SIZE:,} chars)",
                    self.context,
                )

            return String(self.value + suffix).set_context(self.context), None

        return None, self._illegal(other)

    def multed_by(self, other):
        if isinstance(other, Number):
            multiplier_raw = other.value
            if isinstance(multiplier_raw, float) and not multiplier_raw.is_integer():
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    f"String repetition count must be a whole number, got {multiplier_raw}",
                    self.context,
                )

            multiplier = int(multiplier_raw)
            if multiplier < 0:
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    "String repetition count cannot be negative",
                    self.context,
                )

            new_len = len(self.value) * multiplier
            if new_len > String.MAX_STRING_SIZE:
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    f"String repetition result ({new_len:,} chars) exceeds maximum allowed size ({String.MAX_STRING_SIZE:,} chars)",
                    self.context,
                )

            return String(self.value * multiplier).set_context(self.context), None

        return None, self._illegal(other)

    def get_comparison_eq(self, other, visited=None):
        if isinstance(other, String):
            return (
                Number(int(self.value == other.value)).set_context(self.context),
                None,
            )

        return None, self._illegal(other)

    def get_comparison_ne(self, other):
        if isinstance(other, String):
            return (
                Number(int(self.value != other.value)).set_context(self.context),
                None,
            )

        return None, self._illegal(other)

    def get_comparison_lt(self, other):
        if isinstance(other, String):
            return Number(int(self.value < other.value)).set_context(self.context), None

        return None, self._illegal(other)

    def get_comparison_gt(self, other):
        if isinstance(other, String):
            return Number(int(self.value > other.value)).set_context(self.context), None

        return None, self._illegal(other)

    def get_comparison_lte(self, other):
        if isinstance(other, String):
            return (
                Number(int(self.value <= other.value)).set_context(self.context),
                None,
            )

        return None, self._illegal(other)

    def get_comparison_gte(self, other):
        if isinstance(other, String):
            return (
                Number(int(self.value >= other.value)).set_context(self.context),
                None,
            )

        return None, self._illegal(other)

    def get_comparison_is(self, other):
        return Number(1 if self is other else 0).set_context(self.context), None

    def get_comparison_instanceof(self, other):
        from gladlang.values.classes.type_ import Type
        from gladlang.values.classes.class_ import Class

        if isinstance(other, Type):
            if other.name == "String":
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

    def get_element_at(self, index):
        if not isinstance(index, Number):
            return None, RTError(
                self.pos_start,
                self.pos_end,
                "String index must be a Number",
                self.context,
            )

        try:
            val = self.value[int(index.value)]
            return String(val).set_context(self.context), None
        except IndexError:
            return None, RTError(
                self.pos_start,
                self.pos_end,
                f"String index {index.value} out of bounds",
                self.context,
            )

    def anded_by(self, other):
        is_true = self.is_true() and other.is_true()
        return Number(1 if is_true else 0).set_context(self.context), None

    def ored_by(self, other):
        is_true = self.is_true() or other.is_true()
        return Number(1 if is_true else 0).set_context(self.context), None

    def is_true(self):
        return len(self.value) > 0

    def copy(self):
        c = String(self.value)
        c.set_pos(self.pos_start, self.pos_end)
        c.set_context(self.context)
        return c

    def execute(self, args, interpreter=None):
        from gladlang.runtime.rt_result import RTResult

        return RTResult().failure(self._illegal())

    def get_attr(self, name_tok, context=None):
        return None, self._illegal()

    def set_attr(self, name_tok, value, context=None, visibility=None, as_final=False):
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
        return self.value
