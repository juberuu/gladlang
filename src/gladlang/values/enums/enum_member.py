"""EnumMember – a wrapper that represents a single enum case."""

from gladlang.values.primitives.number import Number
from gladlang.values.value import Value


class EnumMember(Value):
    __slots__ = ("enum_name", "member_name", "value", "pos_start", "pos_end", "context")

    def __init__(self, enum_name, member_name, value):
        self.enum_name = enum_name
        self.member_name = member_name
        self.value = value
        self.pos_start = self.pos_end = self.context = None

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def get_attr(self, name_tok, context=None):
        if name_tok.value == "value":
            return self.value, None

        return None, self.illegal_operation()

    def get_comparison_eq(self, other, visited=None):
        if isinstance(other, EnumMember):
            equal = (
                self.enum_name == other.enum_name
                and self.member_name == other.member_name
            )

            return Number(int(equal)).set_context(self.context), None

        return Number(0).set_context(self.context), None

    def get_comparison_ne(self, other):
        eq, err = self.get_comparison_eq(other)
        if err:
            return None, err

        return Number(1 - int(eq.is_true())).set_context(self.context), None

    def get_comparison_is(self, other):
        if isinstance(other, EnumMember):
            equal = (
                self.enum_name == other.enum_name
                and self.member_name == other.member_name
            )

            return Number(int(equal)).set_context(self.context), None

        return Number(0).set_context(self.context), None

    def copy(self):
        c = EnumMember(self.enum_name, self.member_name, self.value)

        return c.set_pos(self.pos_start, self.pos_end).set_context(self.context)

    def __repr__(self):
        return f"{self.enum_name}.{self.member_name}"
