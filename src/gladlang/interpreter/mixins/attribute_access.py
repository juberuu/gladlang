"""Visitors for attribute, list element, and instance creation."""

from gladlang.core.errors import RTError
from gladlang.runtime.rt_result import RTResult
from gladlang.values.classes.class_ import Class


class InterpreterAttributeAccess:
    def visit_GetAttrNode(self, node, context):
        res = RTResult()

        obj = res.register(self.visit(node.object_node, context))
        if res.error:
            return res

        value, error = obj.get_attr(node.attr_name_tok, context)
        if error:
            return res.failure(error)

        return res.success(value.set_pos(node.pos_start, node.pos_end))

    def visit_SetAttrNode(self, node, context):
        res = RTResult()

        obj = res.register(self.visit(node.object_node, context))
        if res.error:
            return res

        value = res.register(self.visit(node.value_node, context))
        if res.error:
            return res

        new_value, error = obj.set_attr(node.attr_name_tok, value, context)
        if error:
            return res.failure(error)

        return res.success(new_value)

    def visit_ListAccessNode(self, node, context):
        res = RTResult()

        list_val = res.register(self.visit(node.list_node, context))
        if res.error:
            return res

        index_val = res.register(self.visit(node.index_node, context))
        if res.error:
            return res

        element, error = list_val.get_element_at(index_val)
        if error:
            error.pos_start = node.pos_start
            error.pos_end = node.pos_end
            return res.failure(error)

        return res.success(element.set_pos(node.pos_start, node.pos_end))

    def visit_ListSetNode(self, node, context):
        res = RTResult()

        list_val = res.register(self.visit(node.list_node, context))
        if res.error:
            return res

        index_val = res.register(self.visit(node.index_node, context))
        if res.error:
            return res

        value_to_set = res.register(self.visit(node.value_node, context))
        if res.error:
            return res

        new_value, error = list_val.set_element_at(index_val, value_to_set)
        if error:
            error.pos_start = node.pos_start
            error.pos_end = node.pos_end
            return res.failure(error)

        return res.success(new_value)

    def visit_NewInstanceNode(self, node, context):
        res = RTResult()

        class_name = node.class_name_tok.value
        class_value = context.symbol_table.get(class_name)
        if not class_value:
            return res.failure(
                RTError(
                    node.pos_start,
                    node.pos_end,
                    f"Class '{class_name}' is not defined",
                    context,
                )
            )

        if not isinstance(class_value, Class):
            return res.failure(
                RTError(
                    node.pos_start,
                    node.pos_end,
                    f"'{class_name}' is not a class",
                    context,
                )
            )

        args = []
        for arg_node in node.arg_nodes:
            args.append(res.register(self.visit(arg_node, context)))
            if res.error:
                return res

        instance = res.register(
            class_value.instantiate(
                args,
                context,
                interpreter=self,
                call_pos_start=node.pos_start,
                call_pos_end=node.pos_end,
                calling_context=context,
            )
        )

        if res.error:
            return res

        return res.success(
            instance.set_pos(node.pos_start, node.pos_end).set_context(context)
        )
