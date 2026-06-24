"""Visitors for variable access, assignment, destructuring, and visibility."""

from gladlang.core.errors import RTError
from gladlang.core.util.final_helpers import is_final_anywhere
from gladlang.runtime.rt_result import RTResult
from gladlang.values.primitives.list import List
from gladlang.values.classes.super_ import Super
from gladlang.values.classes.instance import Instance
from gladlang.parser.ast import (
    VarAssignNode,
    SetAttrNode,
)


class InterpreterVariables:
    def visit_VarAccessNode(self, node, context):
        res = RTResult()

        if context is None:
            return res.failure(
                RTError(
                    node.pos_start,
                    node.pos_end,
                    "Internal error: missing execution context",
                    None,
                )
            )

        var_name = node.var_name_tok.value

        if var_name == "SUPER":
            instance = context.symbol_table.get("THIS")
            if not instance or not isinstance(instance, Instance):
                return res.failure(
                    RTError(
                        node.pos_start,
                        node.pos_end,
                        "'SUPER' can only be used inside an instance method",
                        context,
                    )
                )

            current_class = context.active_class
            if not current_class:
                return res.failure(
                    RTError(
                        node.pos_start,
                        node.pos_end,
                        "'SUPER' cannot be used outside of a class context",
                        context,
                    )
                )

            super_val = (
                Super(instance, current_class)
                .set_context(context)
                .set_pos(node.pos_start, node.pos_end)
            )

            return res.success(super_val)

        if var_name == "THIS" and context.is_static:
            local_this = context.symbol_table.get("THIS")
            if local_this is None:
                return res.failure(
                    RTError(
                        node.pos_start,
                        node.pos_end,
                        "'THIS' cannot be used inside a static method",
                        context,
                    )
                )

        value = context.symbol_table.get(var_name)
        if value is None:
            return res.failure(
                RTError(
                    node.pos_start,
                    node.pos_end,
                    f"'{var_name}' is not defined",
                    context,
                )
            )

        return res.success(value)

    def visit_VarAssignNode(self, node, context):
        res = RTResult()

        if context is None:
            return res.failure(
                RTError(
                    node.pos_start,
                    node.pos_end,
                    "Internal error: missing execution context",
                    None,
                )
            )

        var_name = node.var_name_tok.value
        value = res.register(self.visit(node.value_node, context))
        if res.error:
            return res

        visibility = getattr(node, "target_visibility", "PUBLIC")
        if is_final_anywhere(context.symbol_table, var_name):
            return res.failure(
                RTError(
                    node.var_name_tok.pos_start,
                    node.var_name_tok.pos_end,
                    f"Cannot reassign constant '{var_name}'",
                    context,
                )
            )

        if node.is_declaration:
            context.symbol_table.set(var_name, value, visibility=visibility)
        else:
            err = context.symbol_table.update(var_name, value)
            if err:
                return res.failure(RTError(node.pos_start, node.pos_end, err, context))

        return res.success(value)

    def visit_MultiVarAssignNode(self, node, context):
        res = RTResult()

        list_val = res.register(self.visit(node.value_node, context))
        if res.error:
            return res

        if not isinstance(list_val, List):
            return res.failure(
                RTError(
                    node.pos_start,
                    node.pos_end,
                    f"Cannot unpack type '{type(list_val).__name__}' (expected List)",
                    context,
                )
            )

        if len(node.var_name_toks) != len(list_val.elements):
            return res.failure(
                RTError(
                    node.pos_start,
                    node.pos_end,
                    f"ValueError: too many/not enough values to unpack (expected {len(node.var_name_toks)}, got {len(list_val.elements)})",
                    context,
                )
            )

        for i, var_name_tok in enumerate(node.var_name_toks):
            var_name = var_name_tok.value
            if is_final_anywhere(context.symbol_table, var_name):
                return res.failure(
                    RTError(
                        var_name_tok.pos_start,
                        var_name_tok.pos_end,
                        f"Cannot reassign constant '{var_name}'",
                        context,
                    )
                )

            context.symbol_table.set(var_name, list_val.elements[i])
        return res.success(list_val)

    def visit_FinalVarAssignNode(self, node, context):
        res = RTResult()

        var_name = node.var_name_tok.value
        value = res.register(self.visit(node.value_node, context))
        if res.error:
            return res

        err = context.symbol_table.set_if_absent(var_name, value, as_final=True)
        if err:
            return res.failure(RTError(node.pos_start, node.pos_end, err, context))

        return res.success(value)

    def visit_VisibilityStmtNode(self, node, context):
        res = RTResult()

        target_vis = getattr(node, "target_visibility", node.visibility)
        if target_vis == "FINAL":
            target_vis = "PUBLIC"

        is_final = getattr(node, "is_final", False)

        if isinstance(node.assign_node, SetAttrNode):
            obj = res.register(self.visit(node.assign_node.object_node, context))
            if res.error:
                return res

            val = res.register(self.visit(node.assign_node.value_node, context))
            if res.error:
                return res

            _, error = obj.set_attr(
                node.assign_node.attr_name_tok,
                val,
                context,
                visibility=target_vis,
                as_final=is_final,
            )

            if error:
                return res.failure(error)

            return res.success(val)

        elif isinstance(node.assign_node, VarAssignNode):
            var_name = node.assign_node.var_name_tok.value
            val = res.register(self.visit(node.assign_node.value_node, context))
            if res.error:
                return res

            if is_final:
                err = context.symbol_table.set_if_absent(
                    var_name, val, visibility=target_vis, as_final=True
                )

                if err:
                    return res.failure(
                        RTError(node.pos_start, node.pos_end, err, context)
                    )

                return res.success(val)

            context.symbol_table.set(var_name, val, visibility=target_vis)

            return res.success(val)

        return res.failure(
            RTError(
                node.pos_start, node.pos_end, "Invalid visibility statement", context
            )
        )
