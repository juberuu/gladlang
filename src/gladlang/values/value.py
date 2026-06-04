"""Base Value class – defines the interface for all GladLang runtime objects."""


class Value:
    __slots__ = ("pos_start", "pos_end", "context")

    def __init__(self):
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
        return None, self.illegal_operation(other)

    def subbed_by(self, other):
        return None, self.illegal_operation(other)

    def multed_by(self, other):
        return None, self.illegal_operation(other)

    def dived_by(self, other):
        return None, self.illegal_operation(other)

    def modded_by(self, other):
        return None, self.illegal_operation(other)

    def floordived_by(self, other):
        return None, self.illegal_operation(other)

    def powed_by(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_eq(self, other, visited=None):
        return None, self.illegal_operation(other)

    def get_comparison_ne(self, other):
        from gladlang.values.primitives.number import Number

        result, error = self.get_comparison_eq(other)
        if error:
            return None, error

        if result.is_true():
            return Number(0).set_context(self.context), None
        else:
            return Number(1).set_context(self.context), None

    def get_comparison_lt(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_gt(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_lte(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_gte(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_is(self, other):
        from gladlang.values.primitives.number import Number

        return Number(1 if self is other else 0).set_context(self.context), None

    def get_comparison_instanceof(self, other):
        from gladlang.values.primitives.number import Number
        from gladlang.values.classes.type_ import Type
        from gladlang.values.classes.class_ import Class
        from gladlang.values.primitives.number import Number as Num
        from gladlang.values.primitives.string import String
        from gladlang.values.primitives.list import List
        from gladlang.values.primitives.dict import Dict
        from gladlang.values.functions.base_function import BaseFunction

        if isinstance(other, Type):
            if other.name == "Number" and isinstance(self, Num):
                return Number.true.copy(), None

            if other.name == "String" and isinstance(self, String):
                return Number.true.copy(), None

            if other.name == "List" and isinstance(self, List):
                return Number.true.copy(), None

            if other.name == "Dict" and isinstance(self, Dict):
                return Number.true.copy(), None

            if other.name == "Function" and isinstance(self, BaseFunction):
                return Number.true.copy(), None

            if other.name == "Object":
                return Number.true.copy(), None

            return Number.false.copy(), None

        if isinstance(other, Class):
            return Number.false.copy(), None

        from gladlang.core.errors import RTError

        return None, RTError(
            self.pos_start,
            self.pos_end,
            "Right operand of INSTANCEOF must be a Class or Type",
            self.context,
        )

    def anded_by(self, other):
        from gladlang.values.primitives.number import Number

        is_true = self.is_true() and other.is_true()

        return Number(1 if is_true else 0).set_context(self.context), None

    def ored_by(self, other):
        from gladlang.values.primitives.number import Number

        is_true = self.is_true() or other.is_true()

        return Number(1 if is_true else 0).set_context(self.context), None

    def notted(self):
        return None, self.illegal_operation()

    def execute(self, args, interpreter=None, calling_context=None):
        from gladlang.runtime.rt_result import RTResult

        return RTResult().failure(self.illegal_operation())

    def get_attr(self, name_tok, context=None):
        return None, self.illegal_operation()

    def set_attr(self, name_tok, value, context=None, visibility=None, as_final=False):
        return None, self.illegal_operation()

    def get_element_at(self, index):
        return None, self.illegal_operation()

    def set_element_at(self, index, value):
        return None, self.illegal_operation()

    def is_true(self):
        return True

    def copy(self):
        raise Exception("No copy method defined")

    def bitted_and_by(self, other):
        return None, self.illegal_operation(other)

    def bitted_or_by(self, other):
        return None, self.illegal_operation(other)

    def bitted_xor_by(self, other):
        return None, self.illegal_operation(other)

    def lshifted_by(self, other):
        return None, self.illegal_operation(other)

    def rshifted_by(self, other):
        return None, self.illegal_operation(other)

    def bitted_not(self):
        return None, self.illegal_operation()

    def illegal_operation(self, other=None):
        from gladlang.core.errors import RTError

        if not other:
            other = self

        return RTError(self.pos_start, other.pos_end, "Illegal operation", self.context)
