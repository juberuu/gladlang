"""Super – represents the SUPER keyword for parent method/constructor delegation."""

from gladlang.core.errors import RTError
from gladlang.runtime.rt_result import RTResult
from gladlang.values.primitives.number import Number
from gladlang.values.value import Value


class Super(Value):
    __slots__ = ("instance", "start_class", "pos_start", "pos_end", "context")

    def __init__(self, instance, start_class):
        self.instance = instance
        self.start_class = start_class
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

    def get_attr(self, name_tok, context=None):
        method_name = name_tok.value
        mro = self.instance.class_ref.mro

        try:
            start_index = mro.index(self.start_class) + 1
        except ValueError:
            return None, RTError(
                name_tok.pos_start,
                name_tok.pos_end,
                "Current class not found in MRO",
                context,
            )

        for i in range(start_index, len(mro)):
            cls = mro[i]
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
                        f"Cannot access private method '{method_name}' via SUPER",
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
                            f"Cannot access protected method '{method_name}' via SUPER",
                            context,
                        )

                return method.copy().bind_to_instance(self.instance), None

        return None, RTError(
            name_tok.pos_start,
            name_tok.pos_end,
            f"Method '{method_name}' not found in superclasses",
            context,
        )

    def execute(self, args, interpreter):
        res = RTResult()
        mro = self.instance.class_ref.mro

        try:
            start_index = mro.index(self.start_class) + 1
        except ValueError:
            return res.failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "Current class not found in MRO",
                    self.context,
                )
            )

        method = None
        for i in range(start_index, len(mro)):
            cls = mro[i]
            if cls.name in cls.methods:
                method = cls.methods[cls.name]
                visibility = method.visibility
                defining_class = method.defining_class
                if visibility == "PRIVATE" and (
                    not self.context or self.context.active_class != defining_class
                ):
                    return res.failure(
                        RTError(
                            self.pos_start,
                            self.pos_end,
                            f"Cannot access private constructor of '{cls.name}' via SUPER",
                            self.context,
                        )
                    )

                if visibility == "PROTECTED":
                    allowed = False
                    if self.context and self.context.active_class:
                        if defining_class in self.context.active_class.mro:
                            allowed = True
                        elif not allowed:
                            from gladlang.values.classes.instance import Instance

                            inst = (
                                self.context.symbol_table.get("THIS")
                                if self.context
                                else None
                            )
                            if (
                                inst
                                and isinstance(inst, Instance)
                                and self.context.active_class in inst.class_ref.mro
                            ):
                                allowed = True

                    if not allowed:
                        return res.failure(
                            RTError(
                                self.pos_start,
                                self.pos_end,
                                f"Cannot access protected constructor of '{cls.name}' via SUPER",
                                self.context,
                            )
                        )

                break

        if method:
            result = (
                method.copy().bind_to_instance(self.instance).execute(args, interpreter)
            )

            if result.error:
                return result

            return RTResult().success(Number.null.copy())

        if len(args) > 0:
            return res.failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "No constructor found in superclasses",
                    self.context,
                )
            )

        return res.success(Number.null.copy())

    def copy(self):
        return (
            Super(self.instance, self.start_class)
            .set_context(self.context)
            .set_pos(self.pos_start, self.pos_end)
        )

    def get_comparison_is(self, other):
        return Number(1 if self is other else 0).set_context(self.context), None

    def _illegal(self, other=None):
        if not other:
            other = self

        return RTError(self.pos_start, other.pos_end, "Illegal operation", self.context)

    def illegal_operation(self, other=None):
        return self._illegal(other)
