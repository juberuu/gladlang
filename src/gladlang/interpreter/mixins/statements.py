"""Visitors for control flow statements (if, loops, try, switch, etc.)."""

import sys
from gladlang.core.errors import RTError
from gladlang.runtime.rt_result import RTResult
from gladlang.runtime.context import Context
from gladlang.runtime.symbol_table import SymbolTable
from gladlang.values.primitives.number import Number
from gladlang.values.primitives.string import String
from gladlang.values.primitives.list import List
from gladlang.values.primitives.dict import Dict
from gladlang.values.functions.bound_method import BoundMethod
from gladlang.values.nulls.tailcall import TailCall
from gladlang.parser.ast import CallNode


class InterpreterStatements:
    def visit_StatementListNode(self, node, context):
        res = RTResult()

        last_value = Number.null.copy()

        for statement_node in node.statement_nodes:
            last_value = res.register(self.visit(statement_node, context))
            if (
                res.error
                or res.should_return
                or res.should_break
                or res.should_continue
            ):
                return res

        return res.success(last_value)

    def visit_IfNode(self, node, context):
        res = RTResult()

        for condition, body in node.cases:
            condition_value = res.register(self.visit(condition, context))
            if res.error:
                return res

            if condition_value.is_true():
                expr_value = res.register(self.visit(body, context))
                if res.error:
                    return res

                if res.should_return or res.should_break or res.should_continue:
                    return res

                return res.success(expr_value)

        if node.else_case:
            expr_value = res.register(self.visit(node.else_case, context))
            if res.error:
                return res

            if res.should_return or res.should_break or res.should_continue:
                return res

            return res.success(expr_value)

        return res.success(Number.null.copy())

    def unpack_and_set(self, var_toks, element, context, res):
        if len(var_toks) == 1:
            var_name = var_toks[0].value
            curr_table = context.symbol_table
            while curr_table:
                if var_name in curr_table.finals:
                    return res.failure(
                        RTError(
                            var_toks[0].pos_start,
                            var_toks[0].pos_end,
                            f"Cannot use constant '{var_name}' as loop variable",
                            context,
                        )
                    )

                curr_table = curr_table.parent

            context.symbol_table.set(var_name, element)

            return True

        if not isinstance(element, List):
            return res.failure(
                RTError(
                    var_toks[0].pos_start,
                    var_toks[-1].pos_end,
                    f"Cannot unpack type '{type(element).__name__}' (expected List)",
                    context,
                )
            )

        if len(element.elements) != len(var_toks):
            return res.failure(
                RTError(
                    var_toks[0].pos_start,
                    var_toks[-1].pos_end,
                    f"ValueError: expected {len(var_toks)} values to unpack, got {len(element.elements)}",
                    context,
                )
            )

        for i, tok in enumerate(var_toks):
            var_name = tok.value
            curr_table = context.symbol_table
            while curr_table:
                if var_name in curr_table.finals:
                    return res.failure(
                        RTError(
                            tok.pos_start,
                            tok.pos_end,
                            f"Cannot use constant '{var_name}' as loop variable",
                            context,
                        )
                    )

                curr_table = curr_table.parent

            context.symbol_table.set(var_name, element.elements[i])

        return True

    def get_iterator(self, iterable_val, pos_start, pos_end, context):
        if isinstance(iterable_val, List):
            return iterable_val.elements[:], None
        elif isinstance(iterable_val, String):

            def string_iter(s, ctx, ps, pe):
                for char in s:
                    yield String(char).set_context(ctx).set_pos(ps, pe)

            return string_iter(iterable_val.value, context, pos_start, pos_end), None
        elif isinstance(iterable_val, Dict):
            keys = []
            for k in iterable_val.elements.keys():
                if isinstance(k, (int, float)):
                    keys.append(
                        Number(k).set_context(context).set_pos(pos_start, pos_end)
                    )
                else:
                    keys.append(
                        String(k).set_context(context).set_pos(pos_start, pos_end)
                    )
            return keys, None

        return None, RTError(
            pos_start,
            pos_end,
            f"Type '{type(iterable_val).__name__}' is not iterable (Expected List, String, or Dict)",
            context,
        )

    def visit_ForNode(self, node, context):
        res = RTResult()

        iterable_value = res.register(self.visit(node.iterable_node, context))
        if res.error:
            return res

        iterator, error = self.get_iterator(
            iterable_value,
            node.iterable_node.pos_start,
            node.iterable_node.pos_end,
            context,
        )

        if error:
            return res.failure(error)

        loop_context = Context("FOR", context, node.pos_start)
        loop_context.symbol_table = SymbolTable(context.symbol_table)

        for element in iterator:
            for tok in node.var_name_toks:
                loop_context.symbol_table.remove(tok.value)

            self.unpack_and_set(node.var_name_toks, element, loop_context, res)
            if res.error:
                return res

            value = res.register(self.visit(node.body_node, loop_context))
            if res.error:
                return res

            if res.should_continue:
                res.should_continue = False
                continue

            if res.should_break:
                res.should_break = False
                break

            if res.should_return:
                return res

        return res.success(Number.null.copy())

    def visit_WhileNode(self, node, context):
        res = RTResult()

        loop_context = Context("WHILE", context, node.pos_start)
        loop_context.symbol_table = SymbolTable(context.symbol_table)

        while True:
            condition_value = res.register(
                self.visit(node.condition_node, loop_context)
            )

            if res.error:
                return res

            if not condition_value.is_true():
                break

            value = res.register(self.visit(node.body_node, loop_context))
            if res.error:
                return res

            if res.should_continue:
                res.should_continue = False
                continue

            if res.should_break:
                res.should_break = False
                break

            if res.should_return:
                return res

        return res.success(Number.null.copy())

    def visit_CForNode(self, node, context):
        res = RTResult()

        loop_context = Context("C_FOR", context, node.pos_start)
        loop_context.symbol_table = SymbolTable(context.symbol_table)
        loop_context.active_class = context.active_class

        if node.init_node:
            res.register(self.visit(node.init_node, loop_context))
            if res.error:
                return res

        while True:
            if node.condition_node:
                condition_value = res.register(
                    self.visit(node.condition_node, loop_context)
                )

                if res.error:
                    return res

                if not condition_value.is_true():
                    break

            res.register(self.visit(node.body_node, loop_context))
            if res.error:
                return res

            if res.should_continue:
                res.should_continue = False
            elif res.should_break:
                res.should_break = False
                break
            elif res.should_return:
                return res

            if node.step_node:
                res.register(self.visit(node.step_node, loop_context))
                if res.error:
                    return res

        return res.success(Number.null.copy())

    def visit_BreakNode(self, node, context):
        return RTResult().success_break()

    def visit_ContinueNode(self, node, context):
        return RTResult().success_continue()

    def visit_ReturnNode(self, node, context):
        res = RTResult()

        tco_func = getattr(context, "_tco_func", None)
        if tco_func is not None and isinstance(node.node_to_return, CallNode):
            ret_node = node.node_to_return
            callee = res.register(self.visit(ret_node.node_to_call, context))
            if res.error:
                return res

            tc_args = []
            for arg_node in ret_node.arg_nodes:
                arg_val = res.register(self.visit(arg_node, context))
                if res.error:
                    return res

                tc_args.append(arg_val)

            return res.success_return(TailCall(callee, tc_args))

        value = res.register(self.visit(node.node_to_return, context))
        if res.error:
            return res

        return res.success_return(value)

    def visit_TryCatchNode(self, node, context):
        res = RTResult()

        try_res = self.visit(node.try_body_node, context)

        saved_error = None
        saved_return = None
        saved_should_return = False
        saved_break = False
        saved_continue = False
        saved_value = None

        if try_res.error:
            if node.catch_body_node:
                catch_context = Context("CATCH", context, node.pos_start)
                catch_context.symbol_table = SymbolTable(context.symbol_table)

                if node.catch_var_node:
                    error_msg = try_res.error.details
                    val_to_assign = getattr(try_res.error, "thrown_value", None)

                    if val_to_assign is None:
                        val_to_assign = String(error_msg)

                    catch_context.symbol_table.set(
                        node.catch_var_node.value, val_to_assign
                    )

                catch_result = self.visit(node.catch_body_node, catch_context)
                if catch_result.error:
                    saved_error = catch_result.error

                if catch_result.should_return:
                    saved_should_return = True
                    saved_return = catch_result.return_value

                if catch_result.should_break:
                    saved_break = True

                if catch_result.should_continue:
                    saved_continue = True

            else:
                saved_error = try_res.error
        else:
            if try_res.should_return:
                saved_should_return = True
                saved_return = try_res.return_value
            elif try_res.should_break:
                saved_break = True
            elif try_res.should_continue:
                saved_continue = True
            else:
                saved_value = try_res.value

        if node.finally_body_node:
            finally_result = self.visit(node.finally_body_node, context)
            if finally_result.error:
                return finally_result

            if finally_result.should_return:
                return finally_result

            if finally_result.should_break:
                return RTResult().success_break()

            if finally_result.should_continue:
                return RTResult().success_continue()

        if saved_error:
            return RTResult().failure(saved_error)

        if saved_should_return:
            return RTResult().success_return(saved_return)

        if saved_break:
            return RTResult().success_break()

        if saved_continue:
            return RTResult().success_continue()

        if saved_value is not None:
            return res.success(saved_value)

        return res.success(Number.null.copy())

    def visit_ThrowNode(self, node, context):
        res = RTResult()

        value = res.register(self.visit(node.node_to_throw, context))
        if res.error:
            return res

        return res.failure(
            RTError(
                node.pos_start, node.pos_end, str(value), context, thrown_value=value
            )
        )

    def visit_SwitchNode(self, node, context):
        res = RTResult()

        switch_val = res.register(self.visit(node.switch_value_node, context))
        if res.error:
            return res

        for case_conditions, body_node in node.cases:
            should_execute = False

            for cond_node in case_conditions:
                case_val = res.register(self.visit(cond_node, context))
                if res.error:
                    return res

                is_eq, error = switch_val.get_comparison_eq(case_val)
                if error:
                    return res.failure(error)

                if is_eq.is_true():
                    should_execute = True
                    break

            if should_execute:
                val = res.register(self.visit(body_node, context))
                if res.error:
                    return res

                if res.should_return:
                    return res

                if res.should_break:
                    res.should_break = False
                    return res.success(val)

                if res.should_continue:
                    res.should_continue = False
                    return res.success(val)

                return res.success(val)

        if node.default_case:
            val = res.register(self.visit(node.default_case, context))
            if (
                res.error
                or res.should_return
                or res.should_break
                or res.should_continue
            ):
                return res

            return res.success(val)

        return res.success(Number.null.copy())

    def visit_PrintNode(self, node, context):
        res = RTResult()

        output_strings = []
        for print_node in node.print_nodes:
            value = res.register(self.visit(print_node, context))
            if res.error:
                return res

            output_strings.append(str(value))

        text = " ".join(output_strings)
        if node.should_newline:
            text += "\n"

        sys.stdout.write(text)
        if not node.should_newline:
            sys.stdout.flush()

        return res.success(Number.null.copy())
