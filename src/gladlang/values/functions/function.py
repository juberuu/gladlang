"""Function – user-defined function with closure capture, recursion, and TCO."""

from gladlang.core.errors import RTError
from gladlang.core.util.settings import Settings
from gladlang.runtime.rt_result import RTResult
from gladlang.values.functions.base_function import BaseFunction
from gladlang.values.functions.bound_method import BoundMethod
from gladlang.values.functions.function_group import FunctionGroup
from gladlang.values.nulls.tailcall import TailCall
from gladlang.values.primitives.number import Number


class Function(BaseFunction):
    __slots__ = (
        "body_node",
        "arg_name_toks",
        "arg_names",
        "context",
        "visibility",
        "defining_class",
        "is_static",
        "_call_count",
    )

    def __init__(
        self,
        name,
        body_node,
        arg_name_toks,
        parent_context,
        visibility="PUBLIC",
        defining_class=None,
        is_static=False,
    ):
        super().__init__(name)
        self.body_node = body_node
        self.arg_name_toks = arg_name_toks
        self.arg_names = [tok.value for tok in arg_name_toks]
        self.context = parent_context
        self.visibility = visibility
        self.defining_class = defining_class
        self.is_static = is_static
        self._call_count = 0

    def execute(self, args, interpreter, calling_context=None):
        res = RTResult()

        current_func = self
        current_args = args
        base_depth = None
        final_result = None

        while True:
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

            if hasattr(current_func, "_call_count"):
                current_func._call_count += 1

                if current_func._call_count > Settings.MAX_TOTAL_RECURSION:
                    self._call_count = 0

                    if (
                        hasattr(current_func, "_call_count")
                        and current_func is not self
                    ):
                        current_func._call_count = 0

                    return res.failure(
                        RTError(
                            current_func.pos_start,
                            current_func.pos_end,
                            f"Total recursion calls exceeded limit ({Settings.MAX_TOTAL_RECURSION})",
                            new_context,
                        )
                    )

            if base_depth is None:
                base_depth = new_context.depth
                new_context.parent_entry_pos = self.pos_start

            if new_context.depth > Settings.MAX_CONTEXT_DEPTH:
                self._call_count = 0

                if current_func is not self:
                    current_func._call_count = 0

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
                    getattr(current_func, "arg_names", None), current_args, new_context
                )
            )

            if res.error:
                self._call_count = 0

                if current_func is not self:
                    current_func._call_count = 0

                return res

            value_result = interpreter.visit(current_func.body_node, new_context)

            if value_result.error:
                self._call_count = 0

                if current_func is not self:
                    current_func._call_count = 0

                return value_result

            if value_result.should_return:
                ret_val = value_result.return_value
                if isinstance(ret_val, TailCall):
                    callee = ret_val.function
                    if isinstance(callee, BoundMethod):
                        self._call_count = 0

                        return callee.execute(
                            ret_val.args, interpreter, calling_context
                        )
                    else:
                        current_func = callee
                        current_args = ret_val.args
                        res = RTResult()

                        continue

                final_result = ret_val
                break

            final_result = value_result.value or Number.null.copy()
            break

        self._call_count = 0

        if current_func is not self:
            current_func._call_count = 0

        return res.success(final_result)

    def bind_to_instance(self, instance):
        from gladlang.values.functions.bound_method import BoundMethod

        return BoundMethod(self.name, self, instance)

    def copy(self):
        copy = Function(
            self.name,
            self.body_node,
            self.arg_name_toks,
            self.context,
            self.visibility,
            self.defining_class,
            self.is_static,
        )

        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)

        return copy
