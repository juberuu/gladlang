"""BaseFunction – abstract base for all callable values (functions, methods, classes)."""

from gladlang.core.errors import RTError
from gladlang.runtime.context import Context
from gladlang.runtime.symbol_table import SymbolTable
from gladlang.runtime.rt_result import RTResult
from gladlang.values.value import Value


class BaseFunction(Value):
    __slots__ = ("name", "pos_start", "pos_end", "context")

    def __init__(self, name):
        self.name = name or "<anonymous>"
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

    def generate_new_context(self, calling_context=None):
        parent = calling_context if calling_context is not None else self.context

        new_context = Context(self.name, parent, self.pos_start)
        new_context.symbol_table = SymbolTable(self.context.symbol_table)
        return new_context

    def get_comparison_eq(self, other, visited=None):
        if isinstance(other, BaseFunction):
            return Number(1 if self is other else 0).set_context(self.context), None

        return None, self.illegal_operation(other)

    def get_comparison_ne(self, other):
        if isinstance(other, BaseFunction):
            return Number(1 if self is not other else 0).set_context(self.context), None

        return None, self.illegal_operation(other)

    def get_comparison_is(self, other):
        return Number(1 if self is other else 0).set_context(self.context), None

    def get_comparison_instanceof(self, other):
        from gladlang.values.classes.type_ import Type
        from gladlang.values.classes.class_ import Class

        if isinstance(other, Type):
            if other.name == "Function":
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
        is_true = self.is_true() and other.is_true()
        return Number(1 if is_true else 0).set_context(self.context), None

    def ored_by(self, other):
        is_true = self.is_true() or other.is_true()
        return Number(1 if is_true else 0).set_context(self.context), None

    def check_args(self, arg_names, args):
        res = RTResult()
        if len(args) != len(arg_names):
            return res.failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    f"Incorrect argument count for '{self.name}'. Expected {len(arg_names)}, got {len(args)}",
                    self.context,
                )
            )

        return res.success(None)

    def populate_args(self, arg_names, args, new_context):
        for i in range(len(args)):
            new_context.symbol_table.set(arg_names[i], args[i])

    def check_and_populate_args(self, arg_names, args, new_context):
        res = RTResult()

        if len(args) != len(arg_names):
            return res.failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    f"Incorrect argument count for '{self.name}'. Expected {len(arg_names)}, got {len(args)}",
                    new_context,
                )
            )

        self.populate_args(arg_names, args, new_context)

        return res.success(None)

    def execute(self, args, interpreter, calling_context=None):
        return RTResult().failure(
            RTError(
                self.pos_start,
                self.pos_end,
                "BaseFunction cannot be executed",
                self.context,
            )
        )

    def is_true(self):
        return True

    def copy(self):
        raise Exception("Cannot copy a BaseFunction")

    def get_attr(self, name_tok, context=None):
        return None, self.illegal_operation()

    def set_attr(self, name_tok, value, context=None, visibility=None, as_final=False):
        return None, self.illegal_operation()

    def get_element_at(self, index):
        return None, self.illegal_operation()

    def set_element_at(self, index, value):
        return None, self.illegal_operation()

    def notted(self):
        return None, self.illegal_operation()

    def illegal_operation(self, other=None):
        if not other:
            other = self

        return RTError(self.pos_start, other.pos_end, "Illegal operation", self.context)

    def __repr__(self):
        return f"<function {self.name}>"


from gladlang.values.primitives.number import Number
