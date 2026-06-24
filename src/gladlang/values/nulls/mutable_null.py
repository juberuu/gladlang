"""MutableNull – copy of FrozenNull that can be changed (used for variable assignment)."""

from gladlang.values.primitives.number import Number


class MutableNull(Number):
    __slots__ = ("_is_null",)

    def __init__(self, value, is_null=False):
        super().__init__(value)
        self._is_null = is_null

    def get_comparison_eq(self, other, visited=None):
        from gladlang.values.nulls.frozen_null import FrozenNull

        if isinstance(other, (FrozenNull, MutableNull)):
            return (
                Number(
                    int(self._is_null == other._is_null and self.value == other.value)
                ).set_context(self.context),
                None,
            )

        if isinstance(other, Number):
            if self._is_null:
                return Number(0).set_context(self.context), None

            return (
                Number(int(self.value == other.value)).set_context(self.context),
                None,
            )

        return super().get_comparison_eq(other, visited)

    def get_comparison_ne(self, other):
        eq_result, error = self.get_comparison_eq(other)
        if error:
            return None, error

        return Number(1 - int(eq_result.is_true())).set_context(self.context), None

    def copy(self):
        c = MutableNull(self.value, self._is_null)
        c.set_pos(self.pos_start, self.pos_end)
        c.set_context(self.context)
        return c
