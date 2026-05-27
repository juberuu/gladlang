"""BoundMethod – wraps a function with an instance (self)."""

from gladlang.core.errors import RTError
from gladlang.runtime.rt_result import RTResult
from gladlang.values.functions.base_function import BaseFunction
from gladlang.values.primitives.number import Number


class BoundMethod(BaseFunction):
    __slots__ = (
        "function_to_bind",
        "instance",
        "context",
        "visibility",
        "defining_class",
        "is_static",
    )

    def __init__(self, name, function_to_bind, instance):
        super().__init__(name)
        self.function_to_bind = function_to_bind
        self.instance = instance
        self.context = function_to_bind.context
        self.set_pos(function_to_bind.pos_start, function_to_bind.pos_end)
        self.visibility = getattr(function_to_bind, "visibility", "PUBLIC")
        self.defining_class = getattr(function_to_bind, "defining_class", None)
        self.is_static = getattr(function_to_bind, "is_static", False)

    def bind_to_instance(self, instance):
        return BoundMethod(self.name, self.function_to_bind, instance)

    def execute(self, args, interpreter):
        res = RTResult()
        from gladlang.values.functions.function_group import FunctionGroup
        from gladlang.values.nulls.tailcall import TailCall

        if isinstance(self.function_to_bind, FunctionGroup):
            full_args = [self.instance] + args
            return self.function_to_bind.execute(full_args, interpreter)

        current_func = self.function_to_bind
        current_instance = self.instance
        current_args = args
        base_depth = None

        while True:
            new_context = current_func.generate_new_context()
            new_context.active_class = current_func.defining_class
            new_context.is_static = current_func.is_static

            if base_depth is None:
                base_depth = new_context.depth
                if base_depth > 2000:
                    return res.failure(
                        RTError(
                            current_func.pos_start,
                            current_func.pos_end,
                            "Recursion limit exceeded",
                            current_func.context,
                        )
                    )
            else:
                new_context.depth = base_depth

            new_context._tco_func = current_func

            res.register(
                current_func.check_and_populate_args(
                    current_func.arg_names,
                    [current_instance] + current_args,
                    new_context,
                )
            )

            if res.error:
                return res

            value_result = interpreter.visit(current_func.body_node, new_context)
            if value_result.error:
                return value_result

            if value_result.should_return:
                ret_val = value_result.return_value
                if isinstance(ret_val, TailCall):
                    callee = ret_val.function
                    if isinstance(callee, BoundMethod):
                        current_func = callee.function_to_bind
                        current_instance = callee.instance
                    else:
                        current_func = callee

                    current_args = ret_val.args
                    res = RTResult()

                    continue
                return res.success(ret_val)

            final_val = value_result.value or Number.null.copy()

            return res.success(final_val)

    def copy(self):
        return (
            BoundMethod(self.name, self.function_to_bind.copy(), self.instance)
            .set_context(self.context)
            .set_pos(self.pos_start, self.pos_end)
        )
