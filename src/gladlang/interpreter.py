import sys
from .runtime import RTResult, Context, SymbolTable
from .values import (
    Number,
    String,
    Function,
    Class,
    List,
    Dict,
    FunctionGroup,
    Super,
    Instance,
)
from .nodes import *
from .errors import RTError
from .constants import *


class Interpreter:
    def __init__(self, instruction_limit=None):
        self.dispatch_cache = {}
        self.instruction_limit = instruction_limit

    def visit(self, node, context):
        if self.instruction_limit is not None:
            self.instruction_limit -= 1
            if self.instruction_limit <= 0:
                return RTResult().failure(
                    RTError(
                        node.pos_start,
                        node.pos_end,
                        "Runtime Error: Instruction budget exceeded",
                        context,
                    )
                )

        node_type = type(node)

        method = self.dispatch_cache.get(node_type)

        if method is None:
            method_name = f"visit_{node_type.__name__}"
            method = getattr(self, method_name, self.no_visit_method)
            self.dispatch_cache[node_type] = method

        try:
            result = method(node, context)
        except RecursionError:
            return RTResult().failure(
                RTError(
                    node.pos_start,
                    node.pos_end,
                    "Runtime Error: Expression too complex (maximum recursion depth exceeded)",
                    context,
                )
            )

        if isinstance(result, RTResult) and (
            result.should_return
            or result.should_break
            or result.should_continue
            or result.error
        ):
            return result

        return result

    def no_visit_method(self, node, context):
        raise Exception(f"No visit_{type(node).__name__} method defined")

    def visit_StatementListNode(self, node, context):
        res = RTResult()
        last_value = Number.null

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

            if var_name in context.symbol_table.finals:
                return res.failure(
                    RTError(
                        var_name_tok.pos_start,
                        var_name_tok.pos_end,
                        f"Cannot reassign constant '{var_name}'",
                        context,
                    )
                )

            val = list_val.elements[i]
            context.symbol_table.set(var_name, val)

        return res.success(list_val)

    def visit_ListCompNode(self, node, context):
        res = RTResult()
        output_list = []

        comp_context = Context("COMPREHENSION", context, node.pos_start)
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
                if not self.unpack_and_set(var_toks, element, comp_context, res):
                    return

                if cond_node:
                    condition_res = res.register(self.visit(cond_node, comp_context))
                    if res.error:
                        return
                    if not condition_res.is_true():
                        continue

                evaluate_loops(spec_index + 1)

        evaluate_loops(0)

        if res.error:
            return res

        return res.success(
            List(output_list).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_SliceAccessNode(self, node, context):
        res = RTResult()

        obj = res.register(self.visit(node.node_to_slice, context))
        if res.error:
            return res

        start_val = res.register(self.visit(node.start_node, context))
        if res.error:
            return res

        end_val = None
        if node.end_node:
            end_val = res.register(self.visit(node.end_node, context))
            if res.error:
                return res

        if isinstance(obj, (List, String)):
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

            if end_val:
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
                new_elements = obj.elements[start_idx:end_idx]
                return res.success(
                    List(new_elements)
                    .set_context(context)
                    .set_pos(node.pos_start, node.pos_end)
                )

            elif isinstance(obj, String):
                new_str = obj.value[start_idx:end_idx]
                return res.success(
                    String(new_str)
                    .set_context(context)
                    .set_pos(node.pos_start, node.pos_end)
                )

        return res.failure(
            RTError(
                node.pos_start,
                node.pos_end,
                f"Type {type(obj).__name__} is not sliceable",
                context,
            )
        )

    def visit_VarAccessNode(self, node, context):
        res = RTResult()
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
        var_name = node.var_name_tok.value
        value = res.register(self.visit(node.value_node, context))
        if res.error:
            return res

        visibility = getattr(node, "target_visibility", "PUBLIC")

        if node.is_declaration:
            if var_name in context.symbol_table.finals:
                return res.failure(
                    RTError(
                        node.var_name_tok.pos_start,
                        node.var_name_tok.pos_end,
                        f"Cannot reassign constant '{var_name}'",
                        context,
                    )
                )
            context.symbol_table.set(var_name, value, visibility=visibility)
        else:
            err = context.symbol_table.update(var_name, value)
            if err:
                return res.failure(RTError(node.pos_start, node.pos_end, err, context))

        return res.success(value)

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

        return res.success(Number.null)

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

        return res.success(Number.null)

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
            chars = []
            for char in iterable_val.value:
                chars.append(
                    String(char).set_context(context).set_pos(pos_start, pos_end)
                )
            return chars, None

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
                if not self.unpack_and_set(var_toks, element, comp_context, res):
                    return

                if cond_node:
                    condition_res = res.register(self.visit(cond_node, comp_context))
                    if res.error:
                        return
                    if not condition_res.is_true():
                        continue

                evaluate_loops(spec_index + 1)

        evaluate_loops(0)

        if res.error:
            return res

        return res.success(
            Dict(output_dict).set_context(context).set_pos(node.pos_start, node.pos_end)
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

        for element in iterator:
            loop_context = Context("FOR", context, node.pos_start)
            loop_context.symbol_table = SymbolTable(context.symbol_table)

            if not self.unpack_and_set(node.var_name_toks, element, loop_context, res):
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

        return res.success(Number.null)

    def visit_WhileNode(self, node, context):
        res = RTResult()

        while True:
            condition_value = res.register(self.visit(node.condition_node, context))
            if res.error:
                return res

            if not condition_value.is_true():
                break

            value = res.register(self.visit(node.body_node, context))
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

        return res.success(Number.null)

    def visit_BreakNode(self, node, context):
        return RTResult().success_break()

    def visit_ContinueNode(self, node, context):
        return RTResult().success_continue()

    def visit_FunDefNode(self, node, context):
        res = RTResult()

        func_name = node.var_name_tok.value if node.var_name_tok else None
        body_node = node.body_node

        func = Function(func_name, body_node, node.arg_name_toks, context)

        if func_name:
            existing_val = context.symbol_table.symbols.get(func_name)

            if existing_val and isinstance(existing_val, FunctionGroup):
                existing_val.add_function(func)
                func = existing_val
            elif existing_val and isinstance(existing_val, Function):
                group = FunctionGroup(func_name)
                group.add_function(existing_val)
                group.add_function(func)
                context.symbol_table.set(func_name, group)
                func = group
            else:
                context.symbol_table.set(func_name, func)

        return res.success(
            func.set_pos(node.pos_start, node.pos_end).set_context(context)
        )

    def visit_CallNode(self, node, context):
        res = RTResult()
        args = []

        value_to_call = res.register(self.visit(node.node_to_call, context))
        if res.error:
            return res

        value_to_call = value_to_call.copy().set_pos(node.pos_start, node.pos_end)

        for arg_node in node.arg_nodes:
            args.append(res.register(self.visit(arg_node, context)))
            if res.error:
                return res

        return_value = res.register(value_to_call.execute(args, self))
        if res.error:
            return res

        return res.success(return_value)

    def visit_ReturnNode(self, node, context):
        res = RTResult()

        value = res.register(self.visit(node.node_to_return, context))
        if res.error:
            return res

        return res.success_return(value)

    def visit_ClassNode(self, node, context):
        res = RTResult()

        class_name = node.class_name_tok.value

        superclasses = []
        if node.superclass_nodes:
            for super_node in node.superclass_nodes:
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
                    existing.add_function(method_value)
                else:
                    group = FunctionGroup(method_name)
                    group.add_function(existing)
                    group.add_function(method_value)
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

    def visit_VisibilityStmtNode(self, node, context):
        res = RTResult()

        target_vis = getattr(node, "target_visibility", node.visibility)
        if target_vis == "FINAL":
            target_vis = "PUBLIC"

        if isinstance(node.assign_node, SetAttrNode):
            object_node = node.assign_node.object_node
            attr_name = node.assign_node.attr_name_tok
            value_node = node.assign_node.value_node

            obj = res.register(self.visit(object_node, context))
            if res.error:
                return res

            val = res.register(self.visit(value_node, context))
            if res.error:
                return res

            _, error = obj.set_attr(attr_name, val, context, visibility=node.visibility)
            if error:
                return res.failure(error)

            return res.success(val)

        elif isinstance(node.assign_node, VarAssignNode):
            var_name = node.assign_node.var_name_tok.value

            val = res.register(self.visit(node.assign_node.value_node, context))
            if res.error:
                return res

            if node.visibility == "FINAL":
                if var_name in context.symbol_table.symbols:
                    return res.failure(
                        RTError(
                            node.pos_start,
                            node.pos_end,
                            f"Variable '{var_name}' is already defined",
                            context,
                        )
                    )
                vis_to_use = getattr(node, "target_visibility", "PUBLIC")
                context.symbol_table.set(
                    var_name, val, visibility=vis_to_use, as_final=True
                )
                return res.success(val)

            context.symbol_table.set(var_name, val, visibility=node.visibility)
            return res.success(val)

        return res.failure(
            RTError(
                node.pos_start, node.pos_end, "Invalid visibility statement", context
            )
        )

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
            class_value.instantiate(args, context, interpreter=self)
        )
        if res.error:
            return res

        return res.success(instance.set_pos(node.pos_start, node.pos_end))

    def visit_GetAttrNode(self, node, context):
        res = RTResult()

        object = res.register(self.visit(node.object_node, context))
        if res.error:
            return res

        value, error = object.get_attr(node.attr_name_tok, context)
        if error:
            return res.failure(error)

        return res.success(value.set_pos(node.pos_start, node.pos_end))

    def visit_SetAttrNode(self, node, context):
        res = RTResult()

        object = res.register(self.visit(node.object_node, context))
        if res.error:
            return res

        value = res.register(self.visit(node.value_node, context))
        if res.error:
            return res

        new_value, error = object.set_attr(node.attr_name_tok, value, context)
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
            return res.failure(error)

        return res.success(new_value)

    def visit_BinOpNode(self, node, context):
        res = RTResult()
        left = res.register(self.visit(node.left_node, context))
        if res.error:
            return res

        if node.op_tok.matches(GL_KEYWORD, "AND"):
            if not left.is_true():
                return res.success(Number.false)

            right = res.register(self.visit(node.right_node, context))
            if res.error:
                return res
            result, error = left.anded_by(right)
            if error:
                return res.failure(error)
            return res.success(result.set_pos(node.pos_start, node.pos_end))

        elif node.op_tok.matches(GL_KEYWORD, "OR"):
            if left.is_true():
                return res.success(Number.true)

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

        if node.op_tok.type == GL_PLUS:
            result, error = left.added_to(right)
        elif node.op_tok.type == GL_MINUS:
            result, error = left.subbed_by(right)
        elif node.op_tok.type == GL_MUL:
            result, error = left.multed_by(right)
        elif node.op_tok.type == GL_DIV:
            result, error = left.dived_by(right)
        elif node.op_tok.type == GL_MOD:
            result, error = left.modded_by(right)
        elif node.op_tok.type == GL_FLOORDIV:
            result, error = left.floordived_by(right)
        elif node.op_tok.type == GL_POW:
            result, error = left.powed_by(right)
        elif node.op_tok.type == GL_EE:
            result, error = left.get_comparison_eq(right)
        elif node.op_tok.type == GL_NE:
            result, error = left.get_comparison_ne(right)
        elif node.op_tok.type == GL_LT:
            result, error = left.get_comparison_lt(right)
        elif node.op_tok.type == GL_GT:
            result, error = left.get_comparison_gt(right)
        elif node.op_tok.type == GL_LTE:
            result, error = left.get_comparison_lte(right)
        elif node.op_tok.type == GL_GTE:
            result, error = left.get_comparison_gte(right)
        elif node.op_tok.matches(GL_KEYWORD, "IS"):
            result, error = left.get_comparison_is(right)
        elif node.op_tok.matches(GL_KEYWORD, "INSTANCEOF"):
            result, error = left.get_comparison_instanceof(right)
        elif node.op_tok.type == GL_BIT_AND:
            result, error = left.bitted_and_by(right)
        elif node.op_tok.type == GL_BIT_OR:
            result, error = left.bitted_or_by(right)
        elif node.op_tok.type == GL_BIT_XOR:
            result, error = left.bitted_xor_by(right)
        elif node.op_tok.type == GL_LSHIFT:
            result, error = left.lshifted_by(right)
        elif node.op_tok.type == GL_RSHIFT:
            result, error = left.rshifted_by(right)

        if error:
            return res.failure(error)
        else:
            return res.success(result.set_pos(node.pos_start, node.pos_end))

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
                return res.success(Number.false)

            left_val = right_val

        return res.success(Number.true)

    def visit_UnaryOpNode(self, node, context):
        res = RTResult()

        if node.op_tok.type in (GL_PLUSPLUS, GL_MINUSMINUS):
            target_node = node.node

            if isinstance(target_node, VarAccessNode):
                var_name = target_node.var_name_tok.value

                if var_name in context.symbol_table.finals:
                    return res.failure(
                        RTError(
                            target_node.pos_start,
                            target_node.pos_end,
                            f"Cannot increment/decrement constant '{var_name}'",
                            context,
                        )
                    )

                value = context.symbol_table.get(var_name)
                if not value:
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
            else:
                error = RTError(
                    node.pos_start,
                    node.pos_end,
                    "Unary '-' can only be applied to numbers",
                    context,
                )
        elif node.op_tok.matches(GL_KEYWORD, "NOT"):
            number, error = number.notted()

        elif node.op_tok.type == GL_BIT_NOT:
            number, error = number.bitted_not()

        if error:
            return res.failure(error)
        else:
            return res.success(number.set_pos(node.pos_start, node.pos_end))

    def visit_PostOpNode(self, node, context):
        res = RTResult()
        target_node = node.node

        if isinstance(target_node, VarAccessNode):
            var_name = target_node.var_name_tok.value

            if var_name in context.symbol_table.finals:
                return res.failure(
                    RTError(
                        target_node.pos_start,
                        target_node.pos_end,
                        f"Cannot increment/decrement constant '{var_name}'",
                        context,
                    )
                )

            old_value = context.symbol_table.get(var_name)
            if not old_value:
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

    def visit_TryCatchNode(self, node, context):
        res = RTResult()

        try_res = self.visit(node.try_body_node, context)

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

                catch_res = res.register(
                    self.visit(node.catch_body_node, catch_context)
                )

                if res.error:
                    if node.finally_body_node:
                        fin_res = self.visit(node.finally_body_node, context)
                        if fin_res.error:
                            return res.failure(fin_res.error)

                    return res

            else:
                if node.finally_body_node:
                    fin_res = self.visit(node.finally_body_node, context)
                    if fin_res.error:
                        return fin_res
                return try_res
        else:
            res.register(try_res)
            if res.should_return or res.should_break or res.should_continue:
                if node.finally_body_node:
                    self.visit(node.finally_body_node, context)
                return res

        if node.finally_body_node:
            fin_res = res.register(self.visit(node.finally_body_node, context))
            if res.error:
                return res

        return res.success(Number.null)

    def visit_ThrowNode(self, node, context):
        res = RTResult()

        value = res.register(self.visit(node.node_to_throw, context))
        if res.error:
            return res

        error_message = str(value)

        return res.failure(
            RTError(
                node.pos_start, node.pos_end, error_message, context, thrown_value=value
            )
        )

    def visit_FinalVarAssignNode(self, node, context):
        res = RTResult()
        var_name = node.var_name_tok.value

        if var_name in context.symbol_table.symbols:
            return res.failure(
                RTError(
                    node.pos_start,
                    node.pos_end,
                    f"Variable '{var_name}' is already defined",
                    context,
                )
            )

        value = res.register(self.visit(node.value_node, context))
        if res.error:
            return res

        context.symbol_table.set(var_name, value, as_final=True)
        return res.success(value)

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
                if (
                    res.error
                    or res.should_return
                    or res.should_break
                    or res.should_continue
                ):
                    return res
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

        return res.success(Number.null)
