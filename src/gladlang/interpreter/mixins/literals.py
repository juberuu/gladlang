"""Visitors for literal values and comprehensions."""

from gladlang.core.errors import RTError
from gladlang.runtime.rt_result import RTResult
from gladlang.runtime.context import Context
from gladlang.runtime.symbol_table import SymbolTable
from gladlang.values.primitives.number import Number
from gladlang.values.primitives.string import String
from gladlang.values.primitives.list import List
from gladlang.values.primitives.dict import Dict


class InterpreterLiterals:
    def visit_NumberNode(self, node, context):
        return RTResult().success(
            Number(node.tok.value)
            .set_context(context)
            .set_pos(node.pos_start, node.pos_end)
        )

    def visit_StringNode(self, node, context):
        return RTResult().success(
            String(node.tok.value)
            .set_context(context)
            .set_pos(node.pos_start, node.pos_end)
        )

    def visit_ListNode(self, node, context):
        res = RTResult()

        elements = []
        for element_node in node.element_nodes:
            elements.append(res.register(self.visit(element_node, context)))
            if res.error:
                return res

        return res.success(
            List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_DictNode(self, node, context):
        res = RTResult()

        elements = {}
        for key_node, value_node in node.key_value_pairs:
            key = res.register(self.visit(key_node, context))
            if res.error:
                return res

            value = res.register(self.visit(value_node, context))
            if res.error:
                return res

            if isinstance(key, (Number, String)):
                elements[key.value] = value
            else:
                return res.failure(
                    RTError(
                        key_node.pos_start,
                        key_node.pos_end,
                        "Dictionary key must be a Number or String",
                        context,
                    )
                )

        return res.success(
            Dict(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_ListCompNode(self, node, context):
        res = RTResult()

        output_list = []
        comp_context = Context("LIST_COMPREHENSION", context, node.pos_start)
        comp_context.symbol_table = SymbolTable(context.symbol_table)

        def evaluate_loops(spec_index):
            if spec_index >= len(node.iteration_specs):
                val = res.register(self.visit(node.output_expr_node, comp_context))
                if not res.error:
                    output_list.append(val)

                return

            var_toks, iter_node, cond_node = node.iteration_specs[spec_index]
            iterable_val = res.register(self.visit(iter_node, comp_context))
            if res.error:
                return

            iterator, error = self.get_iterator(
                iterable_val, iter_node.pos_start, iter_node.pos_end, context
            )

            if error:
                res.failure(error)
                return

            for element in iterator:
                for tok in var_toks:
                    comp_context.symbol_table.remove(tok.value)

                self.unpack_and_set(var_toks, element, comp_context, res)
                if res.error:
                    return

                if cond_node:
                    cond_val = res.register(self.visit(cond_node, comp_context))
                    if res.error:
                        return

                    if not cond_val.is_true():
                        continue

                evaluate_loops(spec_index + 1)
                if res.error:
                    return

        evaluate_loops(0)
        if res.error:
            return res

        return res.success(
            List(output_list).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_DictCompNode(self, node, context):
        res = RTResult()

        output_dict = {}
        comp_context = Context("DICT_COMPREHENSION", context, node.pos_start)
        comp_context.symbol_table = SymbolTable(context.symbol_table)

        def evaluate_loops(spec_index):
            if spec_index >= len(node.iteration_specs):
                key_val = res.register(self.visit(node.key_expr_node, comp_context))
                if res.error:
                    return

                val_val = res.register(self.visit(node.value_expr_node, comp_context))
                if res.error:
                    return

                if isinstance(key_val, (Number, String)):
                    output_dict[key_val.value] = val_val
                else:
                    res.failure(
                        RTError(
                            node.key_expr_node.pos_start,
                            node.key_expr_node.pos_end,
                            "Dictionary key must be a Number or String",
                            comp_context,
                        )
                    )
                return

            var_toks, iter_node, cond_node = node.iteration_specs[spec_index]
            iterable_val = res.register(self.visit(iter_node, comp_context))
            if res.error:
                return

            iterator, error = self.get_iterator(
                iterable_val, iter_node.pos_start, iter_node.pos_end, context
            )

            if error:
                res.failure(error)
                return

            for element in iterator:
                for tok in var_toks:
                    comp_context.symbol_table.remove(tok.value)

                self.unpack_and_set(var_toks, element, comp_context, res)
                if res.error:
                    return

                if cond_node:
                    cond_val = res.register(self.visit(cond_node, comp_context))
                    if res.error:
                        return

                    if not cond_val.is_true():
                        continue

                evaluate_loops(spec_index + 1)
                if res.error:
                    return

        evaluate_loops(0)
        if res.error:
            return res

        return res.success(
            Dict(output_dict).set_context(context).set_pos(node.pos_start, node.pos_end)
        )
