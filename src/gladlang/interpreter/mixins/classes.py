"""Visitors for class definitions and MRO computation."""

from gladlang.core.errors import RTError
from gladlang.runtime.rt_result import RTResult
from gladlang.runtime.context import Context
from gladlang.runtime.symbol_table import SymbolTable
from gladlang.values.classes.class_ import Class
from gladlang.values.functions.function import Function
from gladlang.values.functions.function_group import FunctionGroup
from gladlang.parser.ast import VarAccessNode


class InterpreterClasses:
    def visit_ClassNode(self, node, context):
        res = RTResult()

        class_name = node.class_name_tok.value
        superclasses = []

        if node.superclass_nodes:
            for super_node in node.superclass_nodes:
                if (
                    isinstance(super_node, VarAccessNode)
                    and super_node.var_name_tok.value == class_name
                ):
                    return res.failure(
                        RTError(
                            super_node.pos_start,
                            super_node.pos_end,
                            f"Class '{class_name}' cannot inherit from itself",
                            context,
                        )
                    )

                superclass = res.register(self.visit(super_node, context))
                if res.error:
                    return res

                if not isinstance(superclass, Class):
                    return res.failure(
                        RTError(
                            super_node.pos_start,
                            super_node.pos_end,
                            "A class can only inherit from another class",
                            context,
                        )
                    )

                if superclass.name == class_name:
                    return res.failure(
                        RTError(
                            super_node.pos_start,
                            super_node.pos_end,
                            f"Class '{class_name}' cannot inherit from itself",
                            context,
                        )
                    )

                superclasses.append(superclass)

        static_table = SymbolTable(parent=context.symbol_table)
        class_value = Class(class_name, superclasses, {}, static_table)
        class_value.set_context(context).set_pos(node.pos_start, node.pos_end)

        mro, error = self.compute_mro(class_value)
        if error:
            return res.failure(RTError(node.pos_start, node.pos_end, error, context))

        class_value.mro = mro

        class_ctx = Context(f"<class {class_name}>", context, node.pos_start)
        class_ctx.symbol_table = static_table
        class_ctx.active_class = class_value

        for field_node in node.static_field_nodes:
            res.register(self.visit(field_node, class_ctx))
            if res.error:
                return res

        static_table.parent = None

        methods = {}
        for method_node in node.method_nodes:
            method_name = method_node.var_name_tok.value
            method_value = Function(
                method_name,
                method_node.body_node,
                method_node.arg_name_toks,
                context,
                getattr(method_node, "visibility", "PUBLIC"),
                class_value,
                getattr(method_node, "is_static", False),
            ).set_pos(method_node.pos_start, method_node.pos_end)

            if method_name in methods:
                existing = methods[method_name]
                if isinstance(existing, FunctionGroup):
                    err = existing.add_function(method_value)
                    if err and isinstance(err, RTResult) and err.error:
                        return err

                else:
                    group = FunctionGroup(method_name)
                    group.add_function(existing)
                    err = group.add_function(method_value)
                    if err and isinstance(err, RTResult) and err.error:
                        return err

                    methods[method_name] = group
            else:
                methods[method_name] = method_value

            parent_method = None
            for ancestor in class_value.mro:
                if ancestor == class_value:
                    continue

                if method_name in ancestor.methods:
                    parent_method = ancestor.methods[method_name]
                    break

            if parent_method:
                vis_levels = {"PUBLIC": 3, "PROTECTED": 2, "PRIVATE": 1}
                parent_vis_score = vis_levels.get(parent_method.visibility, 3)
                child_vis_score = vis_levels.get(method_value.visibility, 3)

                if child_vis_score < parent_vis_score:
                    return res.failure(
                        RTError(
                            method_node.pos_start,
                            method_node.pos_end,
                            f"Method '{method_name}' cannot be more restrictive than parent method (LSP Violation)",
                            context,
                        )
                    )

        class_value.methods = methods
        class_value._method_cache.clear()

        existing = context.symbol_table.get(class_name)
        if existing is not None and isinstance(existing, Class):
            context.symbol_table.remove(class_name)

        context.symbol_table.set(class_name, class_value)

        return res.success(class_value)

    def compute_mro(self, class_val):
        merge_list = [[class_val]]
        for parent in class_val.superclasses:
            merge_list.append(parent.mro[:])

        merge_list.append(class_val.superclasses[:])
        mro = []

        while True:
            merge_list = [x for x in merge_list if x]
            if not merge_list:
                break

            head = None
            for lst in merge_list:
                candidate = lst[0]
                is_valid = True
                for other_lst in merge_list:
                    if candidate in other_lst[1:]:
                        is_valid = False
                        break

                if is_valid:
                    head = candidate
                    break

            if not head:
                return None, "Inconsistent inheritance hierarchy (Cycle or bad MRO)"

            mro.append(head)
            for lst in merge_list:
                if lst and lst[0] == head:
                    lst.pop(0)

        return mro, None
