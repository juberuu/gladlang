"""Visitor for function definitions."""

from gladlang.core.errors import RTError
from gladlang.core.util.final_helpers import is_final_anywhere
from gladlang.runtime.rt_result import RTResult
from gladlang.values.functions.function import Function
from gladlang.values.functions.function_group import FunctionGroup


class InterpreterFunctions:
    def visit_FunDefNode(self, node, context):
        res = RTResult()

        func_name = node.var_name_tok.value if node.var_name_tok else None
        defining_class = context.active_class

        func = Function(
            func_name,
            node.body_node,
            node.arg_name_toks,
            context,
            visibility=getattr(node, "visibility", "PUBLIC"),
            defining_class=defining_class,
            is_static=getattr(node, "is_static", False),
        )

        if func_name:
            if is_final_anywhere(context.symbol_table, func_name):
                return res.failure(
                    RTError(
                        node.pos_start,
                        node.pos_end,
                        f"Cannot override constant '{func_name}' with a function definition",
                        context,
                    )
                )

            existing_val = context.symbol_table.get(func_name)
            if existing_val and isinstance(existing_val, FunctionGroup):
                err = existing_val.add_function(func)
                if err and isinstance(err, RTResult) and err.error:
                    return err

                func = existing_val

            elif existing_val and isinstance(existing_val, Function):
                group = FunctionGroup(func_name)
                group.add_function(existing_val)
                err = group.add_function(func)
                if err and isinstance(err, RTResult) and err.error:
                    return err

                context.symbol_table.remove(func_name)
                context.symbol_table.set(func_name, group)
                func = group
            else:
                context.symbol_table.set(func_name, func)

        return res.success(
            func.set_pos(node.pos_start, node.pos_end).set_context(context)
        )
