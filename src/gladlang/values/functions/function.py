"""Function – user-defined function with closure capture, recursion, and memoization."""

from gladlang.core.errors import RTError
from gladlang.runtime.rt_result import RTResult
from gladlang.values.functions.base_function import BaseFunction
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
        "_memo_cache",
    )

    MAX_MEMO_SIZE = 10000

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
        self._memo_cache = {}

    def execute(self, args, interpreter):
        res = RTResult()

        from gladlang.values.primitives.string import String
        from gladlang.values.primitives.list import List
        from gladlang.values.primitives.dict import Dict
        from gladlang.values.nulls.frozen_null import FrozenNull
        from gladlang.values.nulls.mutable_null import MutableNull
        from gladlang.values.nulls.tailcall import TailCall
        from gladlang.values.classes.instance import Instance
        from gladlang.values.classes.class_ import Class
        from gladlang.values.functions.bound_method import BoundMethod

        cache_key = None
        can_memoize = True
        arg_values = []
        is_method = self.defining_class is not None and not self.is_static

        if is_method:
            can_memoize = False
        else:
            for arg in args:
                if isinstance(arg, Number):
                    arg_values.append(("Number", arg.value))
                elif isinstance(arg, String):
                    arg_values.append(("String", arg.value))
                elif isinstance(arg, (FrozenNull, MutableNull)):
                    arg_values.append(("Null", None))
                elif isinstance(arg, (List, Dict, Instance, Class, Function)):
                    can_memoize = False
                    break
                else:
                    can_memoize = False
                    break

        if can_memoize:
            cache_key = None
            if self.is_static and self.defining_class:
                static_symbols = self.defining_class.static_symbol_table.symbols
                if any(isinstance(v, (List, Dict)) for v in static_symbols.values()):
                    can_memoize = False
                else:
                    try:
                        static_state = tuple(
                            sorted(
                                (k, v.value if isinstance(v, Number) else v.value)
                                for k, v in static_symbols.items()
                                if isinstance(v, (Number, String))
                            )
                        )
                        cache_key = (self.name, tuple(arg_values), static_state)
                    except Exception:
                        can_memoize = False

            if can_memoize and cache_key is None:
                cache_key = (self.name, tuple(arg_values))

            if can_memoize and cache_key in self._memo_cache:
                cached = self._memo_cache[cache_key].copy()
                cached.set_context(self.context)
                return res.success(cached)

        current_func = self
        current_args = args
        base_depth = None
        final_result = None

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
                    current_func.arg_names, current_args, new_context
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
                    else:
                        current_func = callee
                    current_args = ret_val.args

                    res = RTResult()

                    continue
                final_result = ret_val
                break

            final_result = value_result.value or Number.null.copy()
            break

        if can_memoize and cache_key is not None:
            if len(self._memo_cache) >= self.MAX_MEMO_SIZE:
                self._memo_cache.pop(next(iter(self._memo_cache)))

            self._memo_cache[cache_key] = final_result.copy()

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

        if self.defining_class and self.name == self.defining_class.name:
            copy._memo_cache = {}
        else:
            copy._memo_cache = self._memo_cache

        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy
