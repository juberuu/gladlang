"""MutableNull – copy of FrozenNull that can be changed (used for variable assignment)."""

from gladlang.values.nulls.null_base import NullBase


class MutableNull(NullBase):
    __slots__ = ()

    def __init__(self, value, is_null=False):
        super().__init__(value, is_null)

    def copy(self):
        c = MutableNull(self.value, self._is_null)
        c.set_pos(self.pos_start, self.pos_end)
        c.set_context(self.context)
        return c
