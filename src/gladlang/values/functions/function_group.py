"""FunctionGroup – manages overloaded functions (same name, different arity)."""

from gladlang.core.errors import RTError
from gladlang.runtime.rt_result import RTResult
from gladlang.values.functions.base_function import BaseFunction


class FunctionGroup(BaseFunction):
    __slots__ = ("functions", "visibility", "is_static", "defining_class")

    def __init__(self, name):
        super().__init__(name)
        self.functions = {}
        self.visibility = "PUBLIC"
        self.is_static = False
        self.defining_class = None

    def add_function(self, func):
        arity = len(func.arg_names)
        if arity in self.functions:
            return RTResult().failure(
                RTError(
                    func.pos_start,
                    func.pos_end,
                    f"Overload conflict: '{self.name}' already has a variant with {arity} argument(s)",
                    None,
                )
            )

        self.functions[arity] = func
        if len(self.functions) == 1:
            self.visibility = getattr(func, "visibility", "PUBLIC")
            self.is_static = getattr(func, "is_static", False)
            self.defining_class = getattr(func, "defining_class", None)
        else:
            if getattr(func, "visibility", "PUBLIC") != self.visibility:
                return RTResult().failure(
                    RTError(
                        func.pos_start,
                        func.pos_end,
                        f"All overloads of '{self.name}' must have the same visibility",
                        None,
                    )
                )

        return None

    def execute(self, args, interpreter):
        arity = len(args)
        if arity not in self.functions:
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    f"No variant of function '{self.name}' found that accepts {arity} arguments",
                    self.context,
                )
            )

        return self.functions[arity].execute(args, interpreter)

    def bind_to_instance(self, instance):
        from gladlang.values.functions.bound_method import BoundMethod

        return BoundMethod(self.name, self, instance)

    def copy(self):
        copy = FunctionGroup(self.name)
        copy.visibility = self.visibility
        copy.is_static = self.is_static
        copy.defining_class = self.defining_class
        for arity, func in self.functions.items():
            copy.functions[arity] = func.copy()

        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __repr__(self):
        return f"<function group {self.name}>"
