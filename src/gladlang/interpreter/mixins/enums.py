"""Visitor for enum definitions."""

from gladlang.core.errors import RTError
from gladlang.runtime.rt_result import RTResult
from gladlang.values.enums.enum import Enum
from gladlang.values.primitives.number import Number


class InterpreterEnums:
    def visit_EnumNode(self, node, context):
        res = RTResult()

        enum_name = node.enum_name_tok.value
        elements_dict = {}
        current_val = 0

        for case_name_tok, case_val_node in node.cases:
            case_name = case_name_tok.value
            if case_name in elements_dict:
                return res.failure(
                    RTError(
                        case_name_tok.pos_start,
                        case_name_tok.pos_end,
                        f"Duplicate enum case '{case_name}'",
                        context,
                    )
                )

            if case_val_node:
                val = res.register(self.visit(case_val_node, context))
                if res.error:
                    return res

                if isinstance(val, Number):
                    current_val = int(val.value)

            else:
                val = Number(current_val).set_context(context)
            elements_dict[case_name] = val
            if isinstance(val, Number):
                current_val += 1

        enum_val = Enum(enum_name, elements_dict)
        enum_val.set_context(context).set_pos(node.pos_start, node.pos_end)
        visibility = getattr(node, "visibility", "PUBLIC")

        defining_class = context.active_class if context.active_class else None

        context.symbol_table.set(
            enum_name,
            enum_val,
            visibility=visibility,
            as_final=True,
            defining_class=defining_class,
        )

        return res.success(enum_val)
