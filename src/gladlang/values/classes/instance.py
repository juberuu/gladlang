"""Instance – represents class instances with attribute storage and visibility checks."""

from gladlang.core.errors import RTError
from gladlang.runtime.symbol_table import SymbolTable
from gladlang.runtime.rt_result import RTResult
from gladlang.values.primitives.number import Number
from gladlang.values.value import Value


class Instance(Value):
    __slots__ = ("class_ref", "symbol_table", "pos_start", "pos_end", "context")

    def __init__(self, class_ref):
        self.class_ref = class_ref
        self.symbol_table = SymbolTable()
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

    def is_true(self):
        return True

    def check_access(self, name_tok, visibility, defining_class, context):
        if visibility == "PUBLIC":
            return None

        if visibility == "PRIVATE":
            if not context or context.active_class != defining_class:
                return RTError(
                    name_tok.pos_start,
                    name_tok.pos_end,
                    f"Cannot access private member '{name_tok.value}'",
                    context,
                )

        if visibility == "PROTECTED":
            allowed = False
            if context and context.active_class:
                if defining_class in context.active_class.mro:
                    allowed = True
                elif context.active_class in self.class_ref.mro:
                    allowed = True

            if not allowed:
                return RTError(
                    name_tok.pos_start,
                    name_tok.pos_end,
                    f"Cannot access protected member '{name_tok.value}'",
                    context,
                )

        return None

    def get_attr(self, name_tok, context=None):
        name = name_tok.value

        if context and context.active_class:
            mangled_self = f"_{context.active_class.name}__{name}"
            val = self.symbol_table.get(mangled_self)
            if val is not None:
                return val, None

        if self.class_ref:
            current_class = context.active_class if context else None
            if current_class:
                mangled_current = f"_{current_class.name}__{name}"
                val = self.symbol_table.get(mangled_current)
                if val is not None:
                    return val, None

            for cls in self.class_ref.mro:
                mangled_name = f"_{cls.name}__{name}"
                val = self.symbol_table.get(mangled_name)
                if val is not None:
                    if context and context.active_class == cls:
                        return val, None
                    else:
                        return None, RTError(
                            name_tok.pos_start,
                            name_tok.pos_end,
                            f"Cannot access private member '{name}'",
                            context,
                        )

        value = self.symbol_table.get(name)
        if value is not None:
            visibility = self.symbol_table.get_visibility(name)
            if visibility != "PUBLIC":
                defining_class = self.symbol_table.defining_classes.get(name)
                if defining_class is None:
                    defining_class = self.class_ref

            else:
                defining_class = self.class_ref

            error = self.check_access(name_tok, visibility, defining_class, context)
            if error:
                return None, error

            return value, None

        if context and context.active_class:
            method = context.active_class.methods.get(name)
            if method and method.visibility == "PRIVATE":
                return method.copy().bind_to_instance(self), None

        member, error = self.class_ref.get_attr(name_tok, context, allow_instance=True)
        if error:
            return None, error

        from gladlang.values.functions.base_function import BaseFunction
        from gladlang.values.functions.function import Function

        if isinstance(member, BaseFunction):
            if isinstance(member, Function) and member.is_static:
                return member, None

            if member.visibility == "PRIVATE":
                defining = member.defining_class
                allowed = False
                if context and context.active_class == defining:
                    allowed = True

                if not allowed:
                    return None, RTError(
                        name_tok.pos_start,
                        name_tok.pos_end,
                        f"Cannot access private method '{name_tok.value}'",
                        context,
                    )

            if member.visibility == "PROTECTED":
                defining = getattr(member, "defining_class", None)
                allowed = False
                if context and context.active_class:
                    if defining and defining in context.active_class.mro:
                        allowed = True
                    elif context.active_class in self.class_ref.mro:
                        allowed = True

                if not allowed:
                    return None, RTError(
                        name_tok.pos_start,
                        name_tok.pos_end,
                        f"Cannot access protected method '{name_tok.value}'",
                        context,
                    )

            bound_method = member.copy().bind_to_instance(self)

            return bound_method, None

        return member, None

    def set_attr(self, name_tok, value, context=None, visibility=None, as_final=False):
        name = name_tok.value

        if visibility == "FINAL":
            visibility = "PUBLIC"
            as_final = True

        mangled_name = None
        if context and context.active_class:
            mangled_name = f"_{context.active_class.name}__{name}"

        if visibility is not None or as_final:
            target_name = mangled_name if visibility == "PRIVATE" else name
            if target_name in self.symbol_table.symbols:
                return None, RTError(
                    name_tok.pos_start,
                    name_tok.pos_end,
                    f"Attribute '{name}' is already defined",
                    context,
                )

            self.symbol_table.set(
                target_name,
                value,
                visibility=(visibility or "PUBLIC"),
                as_final=as_final,
                defining_class=context.active_class if context else None,
            )
            if visibility == "PRIVATE" and self.symbol_table.get(name):
                if name in self.symbol_table.finals:
                    return None, RTError(
                        name_tok.pos_start,
                        name_tok.pos_end,
                        f"Cannot shadow constant '{name}' with a private variable",
                        context,
                    )

                self.symbol_table.remove(name)

            return value, None

        if mangled_name and self.symbol_table.get(mangled_name):
            if mangled_name in self.symbol_table.finals:
                return None, RTError(
                    name_tok.pos_start,
                    name_tok.pos_end,
                    f"Cannot reassign constant '{name}'",
                    context,
                )

            err = self.symbol_table.update(mangled_name, value)
            if err:
                return None, RTError(name_tok.pos_start, name_tok.pos_end, err, context)

            return value, None

        if self.symbol_table.get(name):
            current_vis = self.symbol_table.get_visibility(name)
            error = self.check_access(name_tok, current_vis, self.class_ref, context)
            if error:
                return None, error

            if name in self.symbol_table.finals:
                return None, RTError(
                    name_tok.pos_start,
                    name_tok.pos_end,
                    f"Cannot reassign constant '{name}'",
                    context,
                )

            self.symbol_table.set(name, value, visibility=current_vis)

            return value, None

        if self.class_ref.static_symbol_table.get(name):
            if name in self.class_ref.static_symbol_table.finals:
                return None, RTError(
                    name_tok.pos_start,
                    name_tok.pos_end,
                    f"Cannot shadow static constant '{name}' with an instance variable",
                    context,
                )

        err = self.symbol_table.set(name, value, visibility="PUBLIC", as_final=as_final)
        if err:
            return None, RTError(name_tok.pos_start, name_tok.pos_end, err, context)

        return value, None

    def get_comparison_eq(self, other, visited=None):
        if isinstance(other, Instance):
            return Number(1 if self is other else 0).set_context(self.context), None

        return None, self._illegal(other)

    def get_comparison_ne(self, other):
        if isinstance(other, Instance):
            return Number(1 if self is not other else 0).set_context(self.context), None

        return None, self._illegal(other)

    def get_comparison_is(self, other):
        return Number(1 if self is other else 0).set_context(self.context), None

    def get_comparison_instanceof(self, other):
        from gladlang.values.classes.class_ import Class
        from gladlang.values.classes.type_ import Type

        if isinstance(other, Class):
            return (
                Number(1 if other in self.class_ref.mro else 0).set_context(
                    self.context
                ),
                None,
            )

        if isinstance(other, Type):
            if other.name == "Object":
                return Number.true.copy(), None

            return Number.false.copy(), None

        return None, RTError(
            self.pos_start,
            self.pos_end,
            "Right operand of INSTANCEOF must be a Class or Type",
            self.context,
        )

    def anded_by(self, other):
        return (
            Number(1 if (self.is_true() and other.is_true()) else 0).set_context(
                self.context
            ),
            None,
        )

    def ored_by(self, other):
        return (
            Number(1 if (self.is_true() or other.is_true()) else 0).set_context(
                self.context
            ),
            None,
        )

    def execute(self, args, interpreter=None, calling_context=None):
        return RTResult().failure(self._illegal())

    def notted(self):
        return None, self._illegal()

    def copy(self):
        copy = Instance(self.class_ref)
        for name, val in self.symbol_table.symbols.items():
            copy.symbol_table.set(
                name,
                val.copy(),
                visibility=self.symbol_table.get_visibility(name),
                as_final=(name in self.symbol_table.finals),
                defining_class=self.symbol_table.defining_classes.get(name),
            )

        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)

        return copy

    def _illegal(self, other=None):
        if not other:
            other = self

        return RTError(self.pos_start, other.pos_end, "Illegal operation", self.context)

    def illegal_operation(self, other=None):
        return self._illegal(other)

    def __repr__(self):
        return f"<{self.class_ref.name} instance>"
