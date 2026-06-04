"""Visitor for slicing operations on lists and strings."""

from gladlang.core.errors import RTError
from gladlang.runtime.rt_result import RTResult
from gladlang.values.primitives.number import Number
from gladlang.values.primitives.string import String
from gladlang.values.primitives.list import List


class InterpreterSlices:
    def visit_SliceAccessNode(self, node, context):
        res = RTResult()

        obj = res.register(self.visit(node.node_to_slice, context))
        if res.error:
            return res

        start_idx = 0
        if node.start_node is not None:
            start_val = res.register(self.visit(node.start_node, context))
            if res.error:
                return res

            if not isinstance(start_val, Number):
                return res.failure(
                    RTError(
                        node.start_node.pos_start,
                        node.start_node.pos_end,
                        "Start index must be a number",
                        context,
                    )
                )

            start_idx = int(start_val.value)

        end_idx = None
        if node.end_node:
            end_val = res.register(self.visit(node.end_node, context))
            if res.error:
                return res

            if not isinstance(end_val, Number):
                return res.failure(
                    RTError(
                        node.end_node.pos_start,
                        node.end_node.pos_end,
                        "End index must be a number",
                        context,
                    )
                )

            end_idx = int(end_val.value)

        if isinstance(obj, List):
            new_elements = [e.copy() for e in obj.elements[start_idx:end_idx]]
            return res.success(
                List(new_elements)
                .set_context(context)
                .set_pos(node.pos_start, node.pos_end)
            )
        elif isinstance(obj, String):
            return res.success(
                String(obj.value[start_idx:end_idx])
                .set_context(context)
                .set_pos(node.pos_start, node.pos_end)
            )
        else:
            return res.failure(
                RTError(
                    node.pos_start,
                    node.pos_end,
                    f"Type {type(obj).__name__} is not sliceable",
                    context,
                )
            )
