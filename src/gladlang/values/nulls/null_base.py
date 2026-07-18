"""NullBase – base class for null and boolean singletons, providing comparison logic"""

from gladlang.values.primitives.number import Number


class NullBase(Number):
    __slots__ = ("_is_null",)

    def __init__(self, value, is_null=False):
        super().__init__(value)
        self._is_null = is_null

    def get_comparison_eq(self, other, visited=None):
        if hasattr(other, "class_ref") and hasattr(other, "symbol_table"):
            if self._is_null:
                return Number(0).set_context(self.context), None

        if isinstance(other, (NullBase)):
            equal = self._is_null == other._is_null and self.value == other.value
            return Number(int(equal)).set_context(self.context), None

        return Number(0).set_context(self.context), None

    def get_comparison_ne(self, other):
        eq, err = self.get_comparison_eq(other)
        if err:
            return None, err

        return Number(1 - int(eq.is_true())).set_context(self.context), None

    def get_comparison_lt(self, other):
        if self._is_null:
            return None, self._illegal(other)

        return super().get_comparison_lt(other)

    def get_comparison_gt(self, other):
        if self._is_null:
            return None, self._illegal(other)

        return super().get_comparison_gt(other)

    def get_comparison_lte(self, other):
        if self._is_null:
            return None, self._illegal(other)

        return super().get_comparison_lte(other)

    def get_comparison_gte(self, other):
        if self._is_null:
            return None, self._illegal(other)

        return super().get_comparison_gte(other)

    def _illegal(self, other=None):
        if not other:
            other = self

        from gladlang.core.errors import RTError

        return RTError(self.pos_start, other.pos_end, "Illegal operation", self.context)

    def is_true(self):
        if self._is_null:
            return False

        return self.value != 0

    def __repr__(self):
        if self._is_null:
            return "null"

        return str(self.value)
