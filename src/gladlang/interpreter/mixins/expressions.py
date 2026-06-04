"""Visitors for binary, unary, ternary, chained, call, and post‑operations."""

from gladlang.core.constants import (
    GL_KEYWORD,
    GL_PLUSPLUS,
    GL_MINUSMINUS,
    GL_MINUS,
    GL_BIT_NOT,
    GL_EE,
    GL_NE,
    GL_LT,
    GL_GT,
    GL_LTE,
    GL_GTE,
)
from gladlang.core.errors import RTError
from gladlang.core.util.final_helpers import is_final_anywhere
from gladlang.runtime.rt_result import RTResult
from gladlang.values.primitives.number import Number
from gladlang.values.classes.class_ import Class
from gladlang.parser.ast import (
    VarAccessNode,
    GetAttrNode,
    ListAccessNode,
)


class InterpreterExpressions:
    def visit_BinOpNode(self, node, context):
        res = RTResult()

        left = res.register(self.visit(node.left_node, context))
        if res.error:
            return res

        if node.op_tok.matches(GL_KEYWORD, "AND"):
            if not left.is_true():
                return res.success(
                    Number.false.copy()
                    .set_pos(node.pos_start, node.pos_end)
                    .set_context(context)
                )

            right = res.register(self.visit(node.right_node, context))
            if res.error:
                return res

            result, error = left.anded_by(right)
            if error:
                return res.failure(error)

            return res.success(result.set_pos(node.pos_start, node.pos_end))

        elif node.op_tok.matches(GL_KEYWORD, "OR"):
            if left.is_true():
                return res.success(
                    Number.true.copy()
                    .set_pos(node.pos_start, node.pos_end)
                    .set_context(context)
                )

            right = res.register(self.visit(node.right_node, context))
            if res.error:
                return res

            result, error = left.ored_by(right)
            if error:
                return res.failure(error)

            return res.success(result.set_pos(node.pos_start, node.pos_end))

        right = res.register(self.visit(node.right_node, context))
        if res.error:
            return res

        if node.op_tok.matches(GL_KEYWORD, "IS"):
            result, error = left.get_comparison_is(right)
            if error:
                return res.failure(error)

            return res.success(result.set_pos(node.pos_start, node.pos_end))

        elif node.op_tok.matches(GL_KEYWORD, "INSTANCEOF"):
            result, error = left.get_comparison_instanceof(right)
            if error:
                return res.failure(error)

            return res.success(result.set_pos(node.pos_start, node.pos_end))

        op = self._binop_dispatch.get(node.op_tok.type)
        if op is None:
            return res.failure(
                RTError(
                    node.op_tok.pos_start,
                    node.op_tok.pos_end,
                    f"Unsupported operator '{node.op_tok.type}'",
                    context,
                )
            )

        result, error = op(left, right)
        if error:
            error.pos_start = node.pos_start
            error.pos_end = node.pos_end
            error.context = context

            return res.failure(error)

        return res.success(result.set_pos(node.pos_start, node.pos_end))

    def visit_UnaryOpNode(self, node, context):
        res = RTResult()

        if node.op_tok.type in (GL_PLUSPLUS, GL_MINUSMINUS):
            target_node = node.node
            if isinstance(target_node, VarAccessNode):
                var_name = target_node.var_name_tok.value
                if is_final_anywhere(context.symbol_table, var_name):
                    return res.failure(
                        RTError(
                            target_node.pos_start,
                            target_node.pos_end,
                            f"Cannot increment/decrement constant '{var_name}'",
                            context,
                        )
                    )

                value = context.symbol_table.get(var_name)
                if value is None:
                    return res.failure(
                        RTError(
                            target_node.pos_start,
                            target_node.pos_end,
                            f"'{var_name}' is not defined",
                            context,
                        )
                    )

            elif isinstance(target_node, GetAttrNode):
                obj = res.register(self.visit(target_node.object_node, context))
                if res.error:
                    return res

                value, error = obj.get_attr(target_node.attr_name_tok, context)
                if error:
                    return res.failure(error)

            elif isinstance(target_node, ListAccessNode):
                list_val = res.register(self.visit(target_node.list_node, context))
                if res.error:
                    return res

                index_val = res.register(self.visit(target_node.index_node, context))
                if res.error:
                    return res

                value, error = list_val.get_element_at(index_val)
                if error:
                    return res.failure(error)

            else:
                return res.failure(
                    RTError(
                        target_node.pos_start,
                        target_node.pos_end,
                        "Invalid target for increment/decrement",
                        context,
                    )
                )

            if not isinstance(value, Number):
                return res.failure(
                    RTError(
                        target_node.pos_start,
                        target_node.pos_end,
                        "Operand must be a number",
                        context,
                    )
                )

            if node.op_tok.type == GL_PLUSPLUS:
                new_value, error = value.added_to(Number(1))
            else:
                new_value, error = value.subbed_by(Number(1))

            if error:
                return res.failure(error)

            if isinstance(target_node, VarAccessNode):
                err = context.symbol_table.update(var_name, new_value)
                if err:
                    return res.failure(
                        RTError(
                            target_node.pos_start, target_node.pos_end, err, context
                        )
                    )

            elif isinstance(target_node, GetAttrNode):
                _, error = obj.set_attr(target_node.attr_name_tok, new_value, context)
                if error:
                    return res.failure(error)

            elif isinstance(target_node, ListAccessNode):
                _, error = list_val.set_element_at(index_val, new_value)
                if error:
                    return res.failure(error)

            return res.success(new_value.copy().set_pos(node.pos_start, node.pos_end))

        number = res.register(self.visit(node.node, context))
        if res.error:
            return res

        number = number.copy()
        error = None

        if node.op_tok.type == GL_MINUS:
            if isinstance(number, Number):
                number, error = number.multed_by(Number(-1))
                if error:
                    error.pos_start = node.pos_start
                    error.pos_end = node.pos_end
                    error.context = context
            else:
                error = RTError(
                    node.pos_start,
                    node.pos_end,
                    "Unary '-' can only be applied to numbers",
                    context,
                )

        elif node.op_tok.matches(GL_KEYWORD, "NOT"):
            number, error = number.notted()
            if error:
                error.pos_start = node.pos_start
                error.pos_end = node.pos_end
                error.context = context

        elif node.op_tok.type == GL_BIT_NOT:
            number, error = number.bitted_not()
            if error:
                error.pos_start = node.pos_start
                error.pos_end = node.pos_end
                error.context = context

        if error:
            return res.failure(error)

        return res.success(number.set_pos(node.pos_start, node.pos_end))

    def visit_TernaryOpNode(self, node, context):
        res = RTResult()

        condition_value = res.register(self.visit(node.condition_node, context))
        if res.error:
            return res

        if condition_value.is_true():
            result = res.register(self.visit(node.true_case_node, context))
        else:
            result = res.register(self.visit(node.false_case_node, context))

        if res.error:
            return res

        return res.success(result)

    def visit_ChainedCompNode(self, node, context):
        res = RTResult()

        left_val = res.register(self.visit(node.left_node, context))
        if res.error:
            return res

        for op_tok, right_node in node.ops_and_exprs:
            right_val = res.register(self.visit(right_node, context))
            if res.error:
                return res

            result = None
            error = None

            if op_tok.type == GL_EE:
                result, error = left_val.get_comparison_eq(right_val)
            elif op_tok.type == GL_NE:
                result, error = left_val.get_comparison_ne(right_val)
            elif op_tok.type == GL_LT:
                result, error = left_val.get_comparison_lt(right_val)
            elif op_tok.type == GL_GT:
                result, error = left_val.get_comparison_gt(right_val)
            elif op_tok.type == GL_LTE:
                result, error = left_val.get_comparison_lte(right_val)
            elif op_tok.type == GL_GTE:
                result, error = left_val.get_comparison_gte(right_val)
            elif op_tok.matches(GL_KEYWORD, "IS"):
                result, error = left_val.get_comparison_is(right_val)

            if error:
                return res.failure(error)

            if not result.is_true():
                return res.success(Number.false.copy())

            left_val = right_val

        return res.success(Number.true.copy())

    def visit_PostOpNode(self, node, context):
        res = RTResult()

        target_node = node.node
        if isinstance(target_node, VarAccessNode):
            var_name = target_node.var_name_tok.value
            if is_final_anywhere(context.symbol_table, var_name):
                return res.failure(
                    RTError(
                        target_node.pos_start,
                        target_node.pos_end,
                        f"Cannot increment/decrement constant '{var_name}'",
                        context,
                    )
                )

            old_value = context.symbol_table.get(var_name)
            if old_value is None:
                return res.failure(
                    RTError(
                        target_node.pos_start,
                        target_node.pos_end,
                        f"'{var_name}' is not defined",
                        context,
                    )
                )

        elif isinstance(target_node, GetAttrNode):
            obj = res.register(self.visit(target_node.object_node, context))
            if res.error:
                return res

            old_value, error = obj.get_attr(target_node.attr_name_tok, context)
            if error:
                return res.failure(error)

        elif isinstance(target_node, ListAccessNode):
            list_val = res.register(self.visit(target_node.list_node, context))
            if res.error:
                return res

            index_val = res.register(self.visit(target_node.index_node, context))
            if res.error:
                return res

            old_value, error = list_val.get_element_at(index_val)
            if error:
                return res.failure(error)

        else:
            return res.failure(
                RTError(
                    target_node.pos_start,
                    target_node.pos_end,
                    "Invalid target for increment/decrement",
                    context,
                )
            )

        if not isinstance(old_value, Number):
            return res.failure(
                RTError(
                    target_node.pos_start,
                    target_node.pos_end,
                    "Operand must be a number",
                    context,
                )
            )

        if node.op_tok.type == GL_PLUSPLUS:
            new_value, error = old_value.added_to(Number(1))
        else:
            new_value, error = old_value.subbed_by(Number(1))

        if error:
            return res.failure(error)

        if isinstance(target_node, VarAccessNode):
            err = context.symbol_table.update(var_name, new_value)
            if err:
                return res.failure(
                    RTError(target_node.pos_start, target_node.pos_end, err, context)
                )

        elif isinstance(target_node, GetAttrNode):
            _, error = obj.set_attr(target_node.attr_name_tok, new_value, context)
            if error:
                return res.failure(error)

        elif isinstance(target_node, ListAccessNode):
            _, error = list_val.set_element_at(index_val, new_value)
            if error:
                return res.failure(error)

        return res.success(old_value.copy().set_pos(node.pos_start, node.pos_end))

    def visit_CallNode(self, node, context):
        res = RTResult()

        args = []
        value_to_call = res.register(self.visit(node.node_to_call, context))
        if res.error:
            return res

        value_to_call = value_to_call.set_pos(node.pos_start, node.pos_end)
        if value_to_call.context is None or isinstance(value_to_call, Class):
            value_to_call = value_to_call.copy()
            value_to_call.set_context(context)

        for arg_node in node.arg_nodes:
            args.append(res.register(self.visit(arg_node, context)))
            if res.error:
                return res

        return_value = res.register(value_to_call.execute(args, self, context))
        if res.error:
            return res

        return res.success(return_value)
