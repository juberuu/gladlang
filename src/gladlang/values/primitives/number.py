"""Number – numeric type (int/float) with arithmetic, bitwise, and comparison operations."""

import math
from gladlang.core.errors import RTError
from gladlang.values.value import Value


class Number(Value):
    MAX_INT_BITS = 100_000

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
        if isinstance(other, Number):
            result = self.value + other.value
            if isinstance(result, int) and result.bit_length() > Number.MAX_INT_BITS:
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    "Arithmetic result too large (exceeds integer size limit)",
                    self.context,
                )

            if isinstance(result, float) and math.isinf(result):
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    "Arithmetic result is infinite (float overflow)",
                    self.context,
                )

            return Number(result).set_context(self.context), None

        from gladlang.values.primitives.string import String

        if isinstance(other, String):
            return String(str(self.value) + other.value).set_context(self.context), None

        return None, self._illegal(other)

    def subbed_by(self, other):
        if isinstance(other, Number):
            result = self.value - other.value
            if isinstance(result, int) and result.bit_length() > Number.MAX_INT_BITS:
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    "Arithmetic result too large (exceeds integer size limit)",
                    self.context,
                )

            if isinstance(result, float) and math.isinf(result):
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    "Arithmetic result is infinite (float overflow)",
                    self.context,
                )

            return Number(result).set_context(self.context), None

        return None, self._illegal(other)

    def multed_by(self, other):
        if isinstance(other, Number):
            result = self.value * other.value
            if isinstance(result, int) and result.bit_length() > Number.MAX_INT_BITS:
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    "Arithmetic result too large (exceeds integer size limit)",
                    self.context,
                )

            if isinstance(result, float) and math.isinf(result):
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    "Arithmetic result is infinite (float overflow)",
                    self.context,
                )

            return Number(result).set_context(self.context), None

        return None, self._illegal(other)

    def dived_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RTError(
                    other.pos_start, other.pos_end, "Division by zero", self.context
                )

            try:
                result = self.value / other.value
            except OverflowError:
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    "Division result exceeds float range; use integer floor division (//) instead",
                    self.context,
                )

            if math.isinf(result):
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    "Arithmetic result is infinite (float overflow)",
                    self.context,
                )

            return Number(result).set_context(self.context), None

        return None, self._illegal(other)

    def modded_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RTError(
                    other.pos_start, other.pos_end, "Division by zero", self.context
                )

            result = self.value % other.value
            if isinstance(result, int) and result.bit_length() > Number.MAX_INT_BITS:
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    "Arithmetic result too large (exceeds integer size limit)",
                    self.context,
                )

            return Number(result).set_context(self.context), None

        return None, self._illegal(other)

    def floordived_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RTError(
                    other.pos_start, other.pos_end, "Division by zero", self.context
                )

            result = self.value // other.value
            if isinstance(result, int) and result.bit_length() > Number.MAX_INT_BITS:
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    "Arithmetic result too large (exceeds integer size limit)",
                    self.context,
                )

            return Number(result).set_context(self.context), None

        return None, self._illegal(other)

    def powed_by(self, other):
        if isinstance(other, Number):
            if other.value > 10000:
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    "Exponent too large (limit: 10000)",
                    self.context,
                )

            try:
                result = self.value**other.value
            except (ValueError, ZeroDivisionError, OverflowError) as e:
                return None, RTError(
                    other.pos_start, other.pos_end, str(e), self.context
                )

            if isinstance(result, complex):
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    "Math domain error: result is complex",
                    self.context,
                )

            if isinstance(result, float) and math.isnan(result):
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    "Math domain error: result is NaN",
                    self.context,
                )

            if isinstance(result, float) and math.isinf(result):
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    "Arithmetic result is infinite (float overflow)",
                    self.context,
                )

            return Number(result).set_context(self.context), None

        return None, self._illegal(other)

    def get_comparison_is(self, other):
        return Number(1 if self is other else 0).set_context(self.context), None

    def get_comparison_eq(self, other, visited=None):
        if isinstance(other, Number):
            return (
                Number(int(self.value == other.value)).set_context(self.context),
                None,
            )

        return None, self._illegal(other)

    def get_comparison_ne(self, other):
        if isinstance(other, Number):
            return (
                Number(int(self.value != other.value)).set_context(self.context),
                None,
            )

        return None, self._illegal(other)

    def get_comparison_lt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value < other.value)).set_context(self.context), None

        return None, self._illegal(other)

    def get_comparison_gt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value > other.value)).set_context(self.context), None

        return None, self._illegal(other)

    def get_comparison_lte(self, other):
        if isinstance(other, Number):
            return (
                Number(int(self.value <= other.value)).set_context(self.context),
                None,
            )

        return None, self._illegal(other)

    def get_comparison_gte(self, other):
        if isinstance(other, Number):
            return (
                Number(int(self.value >= other.value)).set_context(self.context),
                None,
            )

        return None, self._illegal(other)

    def anded_by(self, other):
        if isinstance(other, Number):
            return Number(1 if (self.is_true() and other.is_true()) else 0), None

        return None, self._illegal(other)

    def ored_by(self, other):
        if isinstance(other, Number):
            return Number(1 if (self.is_true() or other.is_true()) else 0), None

        return None, self._illegal(other)

    def notted(self):
        return (Number(0), None) if self.is_true() else (Number(1), None)

    def bitted_and_by(self, other):
        if isinstance(other, Number):
            raw = (int(self.value) & int(other.value)) & 0xFFFFFFFF
            if raw & 0x80000000:
                raw -= 0x100000000

            return Number(raw).set_context(self.context), None

        return None, self._illegal(other)

    def bitted_or_by(self, other):
        if isinstance(other, Number):
            raw = (int(self.value) | int(other.value)) & 0xFFFFFFFF
            if raw & 0x80000000:
                raw -= 0x100000000

            return Number(raw).set_context(self.context), None

        return None, self._illegal(other)

    def bitted_xor_by(self, other):
        if isinstance(other, Number):
            raw = (int(self.value) ^ int(other.value)) & 0xFFFFFFFF
            if raw & 0x80000000:
                raw -= 0x100000000

            return Number(raw).set_context(self.context), None

        return None, self._illegal(other)

    def lshifted_by(self, other):
        if isinstance(other, Number):
            shift_amount = int(other.value)
            if shift_amount < 0:
                return None, RTError(
                    other.pos_start, other.pos_end, "Negative shift count", self.context
                )

            if shift_amount >= 32:
                return Number(0).set_context(self.context), None

            raw = (int(self.value) << shift_amount) & 0xFFFFFFFF
            if raw & 0x80000000:
                raw -= 0x100000000

            return Number(raw).set_context(self.context), None

        return None, self._illegal(other)

    def rshifted_by(self, other):
        if isinstance(other, Number):
            shift_amount = int(other.value)
            if shift_amount < 0:
                return None, RTError(
                    other.pos_start, other.pos_end, "Negative shift count", self.context
                )

            if shift_amount >= 32:
                return (Number(-1) if int(self.value) < 0 else Number(0)).set_context(
                    self.context
                ), None

            raw = int(self.value) >> shift_amount
            masked = raw & 0xFFFFFFFF
            result = masked - 0x100000000 if masked & 0x80000000 else masked

            return Number(result).set_context(self.context), None

        return None, self._illegal(other)

    def bitted_not(self):
        raw = (~int(self.value)) & 0xFFFFFFFF
        if raw & 0x80000000:
            raw -= 0x100000000

        return Number(raw).set_context(self.context), None

    def get_comparison_instanceof(self, other):
        from gladlang.values.classes.type_ import Type
        from gladlang.values.classes.class_ import Class

        if isinstance(other, Type):
            if other.name == "Number":
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

    def is_true(self):
        return self.value != 0

    def copy(self):
        c = Number(self.value)
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

    def get_element_at(self, index):
        return None, self._illegal()

    def set_element_at(self, index, value):
        return None, self._illegal()

    def _illegal(self, other=None):
        if not other:
            other = self

        return RTError(self.pos_start, other.pos_end, "Illegal operation", self.context)

    def illegal_operation(self, other=None):
        return self._illegal(other)

    def __repr__(self):
        return str(self.value)


Number.false = None
Number.true = None
Number.null = None
