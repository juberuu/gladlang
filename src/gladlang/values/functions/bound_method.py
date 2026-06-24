"""BoundMethod – wraps a function with an instance (self)."""

from gladlang.core.errors import RTError
from gladlang.runtime.rt_result import RTResult
from gladlang.values.functions.base_function import BaseFunction
from gladlang.values.primitives.number import Number


class BoundMethod(BaseFunction):
    MAX_TOTAL_RECURSION = 10000

    __slots__ = (
        "function_to_bind",
        "instance",
        "context",
        "visibility",
        "defining_class",
        "is_static",
        "_call_count",
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
        self._call_count = 0

    def bind_to_instance(self, instance):
        return BoundMethod(self.name, self.function_to_bind, instance)

    def execute(self, args, interpreter, calling_context=None):
        res = RTResult()

        from gladlang.values.functions.function_group import FunctionGroup
        from gladlang.values.nulls.tailcall import TailCall

        if isinstance(self.function_to_bind, FunctionGroup):
            full_args = [self.instance] + args
            fg = self.function_to_bind

            if fg.context is None or fg.pos_start is None:
                fg = fg.copy()
                if self.context is not None:
                    fg.set_context(self.context)

                fg.set_pos(self.pos_start, self.pos_end)

            return fg.execute(full_args, interpreter, calling_context)

        current_func = self.function_to_bind
        current_instance = self.instance
        current_args = args
        base_depth = None

        while True:
            from gladlang.values.functions.function_group import FunctionGroup

            if isinstance(current_func, FunctionGroup):
                arity = len(current_args)
                if arity in current_func.functions:
                    current_func = current_func.functions[arity]
                else:
                    return res.failure(
                        RTError(
                            current_func.pos_start,
                            current_func.pos_end,
                            f"No variant of function '{current_func.name}' accepts {arity} arguments",
                            self.context,
                        )
                    )

            if not hasattr(current_func, "body_node"):
                return current_func.execute(current_args, interpreter, calling_context)

            new_context = current_func.generate_new_context(
                calling_context if base_depth is None else None
            )

            new_context.active_class = getattr(current_func, "defining_class", None)
            new_context.is_static = getattr(current_func, "is_static", False)

            self._call_count += 1

            if self._call_count > BoundMethod.MAX_TOTAL_RECURSION:
                self._call_count = 0
                return res.failure(
                    RTError(
                        current_func.pos_start,
                        current_func.pos_end,
                        f"Total recursion calls exceeded limit ({BoundMethod.MAX_TOTAL_RECURSION})",
                        new_context,
                    )
                )

            if base_depth is None:
                base_depth = new_context.depth
                new_context.parent_entry_pos = self.pos_start

            if new_context.depth > 2000:
                self._call_count = 0
                return res.failure(
                    RTError(
                        current_func.pos_start,
                        current_func.pos_end,
                        "Recursion limit exceeded",
                        new_context,
                    )
                )

            new_context._tco_func = current_func

            res.register(
                current_func.check_and_populate_args(
                    getattr(current_func, "arg_names", None),
                    [current_instance] + current_args,
                    new_context,
                )
            )

            if res.error:
                self._call_count = 0
                return res

            value_result = interpreter.visit(current_func.body_node, new_context)
            if value_result.error:
                self._call_count = 0
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

                self._call_count = 0
                return res.success(ret_val)

            final_val = value_result.value or Number.null.copy()
            self._call_count = 0

            return res.success(final_val)

    def copy(self):
        return (
            BoundMethod(self.name, self.function_to_bind.copy(), self.instance)
            .set_context(self.context)
            .set_pos(self.pos_start, self.pos_end)
        )
