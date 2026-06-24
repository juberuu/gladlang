"""Class – represents user-defined classes with methods, inheritance, and MRO."""

from gladlang.core.errors import RTError
from gladlang.runtime.symbol_table import SymbolTable
from gladlang.runtime.rt_result import RTResult
from gladlang.values.functions.base_function import BaseFunction


class Class(BaseFunction):
    __slots__ = (
        "superclasses",
        "methods",
        "static_symbol_table",
        "mro",
        "_method_cache",
    )

    def __init__(self, name, superclasses, methods, static_symbol_table=None, mro=None):
        super().__init__(name)
        self.superclasses = superclasses
        self.methods = methods
        self.static_symbol_table = (
            static_symbol_table if static_symbol_table else SymbolTable()
        )
        self.mro = mro if mro else [self]
        self._method_cache = {}

    def instantiate(
        self,
        args,
        context=None,
        interpreter=None,
        call_pos_start=None,
        call_pos_end=None,
        calling_context=None,
    ):
        res = RTResult()

        from gladlang.values.classes.instance import Instance
        from gladlang.values.functions.function import Function
        from gladlang.core.constants import GL_IDENTIFIER
        from gladlang.lexer.token import Token

        instance = Instance(self)
        constructor_name = None

        for cls in self.mro:
            if cls.name in cls.methods:
                constructor_name = cls.name
                break

        if constructor_name:
            fake_tok = Token(
                GL_IDENTIFIER, constructor_name, self.pos_start, self.pos_end
            )

            init_method, error = self.get_attr(fake_tok, context, allow_instance=True)
            if error:
                return res.failure(error)

            bound_init = init_method.copy().bind_to_instance(instance)
            if call_pos_start is not None:
                bound_init.set_pos(call_pos_start, call_pos_end)

            res.register(bound_init.execute(args, interpreter, calling_context))
            if res.error:
                return res

        else:
            if len(args) > 0:
                return res.failure(
                    RTError(
                        call_pos_start or self.pos_start,
                        call_pos_end or self.pos_end,
                        f"'{self.name}' does not have a constructor that accepts arguments",
                        context or self.context,
                    )
                )

        return res.success(instance)

    def execute(self, args, interpreter=None, calling_context=None):
        return RTResult().failure(
            RTError(
                self.pos_start,
                self.pos_end,
                f"Class '{self.name}' must be instantiated using 'NEW'",
                self.context,
            )
        )

    def set_attr(self, name_tok, value, context=None, visibility=None, as_final=False):
        name = name_tok.value
        if visibility == "FINAL":
            visibility = "PUBLIC"
            as_final = True

        existing = self.static_symbol_table.get(name)
        if existing is not None:
            if name in self.static_symbol_table.finals:
                return None, RTError(
                    name_tok.pos_start,
                    name_tok.pos_end,
                    f"Cannot reassign static constant '{name}'",
                    context,
                )

            err = self.static_symbol_table.update(name, value)
            if err:
                return None, RTError(name_tok.pos_start, name_tok.pos_end, err, context)

            self._method_cache.clear()

            return value, None
        else:
            self.static_symbol_table.set(
                name,
                value,
                visibility=(visibility or "PUBLIC"),
                as_final=as_final,
                defining_class=self,
            )
            self._method_cache.clear()
            return value, None

    def get_attr(self, name_tok, context=None, allow_instance=False):
        method_name = name_tok.value
        active_class = (
            context.active_class if context and context.active_class else None
        )

        cache_key = (method_name, allow_instance)

        if cache_key in self._method_cache:
            cached_value, cached_vis, cached_def, cached_kind = self._method_cache[
                cache_key
            ]

            from gladlang.values.functions.base_function import BaseFunction
            from gladlang.values.functions.bound_method import BoundMethod

            def _check_vis(vis, def_cls, kind):
                if vis == "PRIVATE":
                    if (
                        not context
                        or not context.active_class
                        or context.active_class != def_cls
                    ):
                        msg = (
                            f"Cannot access private static field '{method_name}'"
                            if kind == "field"
                            else f"Cannot access private method '{method_name}' via Class"
                        )
                        return RTError(
                            name_tok.pos_start,
                            name_tok.pos_end,
                            msg,
                            context,
                        )

                elif vis == "PROTECTED":
                    allowed = False
                    if context and context.active_class:
                        if def_cls in context.active_class.mro:
                            allowed = True
                        elif not allowed:
                            from gladlang.values.classes.instance import Instance

                            inst = context.symbol_table.get("THIS") if context else None

                            if (
                                inst
                                and isinstance(inst, Instance)
                                and context.active_class in inst.class_ref.mro
                            ):
                                allowed = True

                    if not allowed:
                        msg = (
                            f"Cannot access protected static field '{method_name}'"
                            if kind == "field"
                            else f"Cannot access protected method '{method_name}' via Class"
                        )
                        return RTError(
                            name_tok.pos_start,
                            name_tok.pos_end,
                            msg,
                            context,
                        )

                return None

            err = _check_vis(cached_vis, cached_def, cached_kind)
            if err:
                return None, err

            if isinstance(cached_value, (BaseFunction, BoundMethod)):
                return cached_value.copy(), None

            return cached_value, None

        for cls in self.mro:
            val = cls.static_symbol_table.get(method_name)
            if val is not None:
                visibility = cls.static_symbol_table.get_visibility(method_name)
                defining_class = cls
                if visibility == "PRIVATE" and (
                    not context or context.active_class != defining_class
                ):
                    return None, RTError(
                        name_tok.pos_start,
                        name_tok.pos_end,
                        f"Cannot access private static field '{method_name}'",
                        context,
                    )

                if visibility == "PROTECTED":
                    allowed = False
                    if context and context.active_class:
                        if defining_class in context.active_class.mro:
                            allowed = True
                        elif not allowed:
                            from gladlang.values.classes.instance import Instance

                            inst = context.symbol_table.get("THIS") if context else None

                            if (
                                inst
                                and isinstance(inst, Instance)
                                and context.active_class in inst.class_ref.mro
                            ):
                                allowed = True

                    if not allowed:
                        return None, RTError(
                            name_tok.pos_start,
                            name_tok.pos_end,
                            f"Cannot access protected static field '{method_name}'",
                            context,
                        )

                self._method_cache[cache_key] = (
                    val,
                    visibility,
                    defining_class,
                    "field",
                )
                return val, None

            method = cls.methods.get(method_name)
            if method:
                visibility = method.visibility
                defining_class = method.defining_class
                if visibility == "PRIVATE" and (
                    not context or context.active_class != defining_class
                ):
                    return None, RTError(
                        name_tok.pos_start,
                        name_tok.pos_end,
                        f"Cannot access private method '{method_name}' via Class",
                        context,
                    )

                if visibility == "PROTECTED":
                    allowed = False
                    if context and context.active_class:
                        if defining_class in context.active_class.mro:
                            allowed = True
                        elif not allowed:
                            from gladlang.values.classes.instance import Instance

                            inst = context.symbol_table.get("THIS") if context else None

                            if (
                                inst
                                and isinstance(inst, Instance)
                                and context.active_class in inst.class_ref.mro
                            ):
                                allowed = True

                    if not allowed:
                        return None, RTError(
                            name_tok.pos_start,
                            name_tok.pos_end,
                            f"Cannot access protected method '{method_name}' via Class",
                            context,
                        )

                if method.is_static:
                    result = (
                        method.copy()
                        .set_context(self.context)
                        .set_pos(name_tok.pos_start, name_tok.pos_end)
                    )
                    self._method_cache[cache_key] = (
                        result,
                        visibility,
                        defining_class,
                        "method",
                    )
                    return result, None

                if context:
                    from gladlang.values.classes.instance import Instance

                    instance = context.symbol_table.get("THIS")

                    if (
                        instance
                        and isinstance(instance, Instance)
                        and self in instance.class_ref.mro
                    ):
                        bound = method.copy().bind_to_instance(instance)
                        self._method_cache[cache_key] = (
                            bound,
                            visibility,
                            defining_class,
                            "method",
                        )

                        return bound, None

                self._method_cache[cache_key] = (
                    method.copy(),
                    visibility,
                    defining_class,
                    "method",
                )

                return method.copy(), None

        return None, RTError(
            name_tok.pos_start,
            name_tok.pos_end,
            f"Class '{self.name}' has no member '{method_name}'",
            context,
        )

    def copy(self):
        copy = Class(
            self.name,
            self.superclasses[:],
            self.methods,
            self.static_symbol_table.copy(),
            self.mro[:],
        )

        copy._method_cache = self._method_cache
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)

        return copy

    def __repr__(self):
        return f"<class {self.name}>"
