class StatementListNode:
    def __init__(self, statement_nodes, pos_start, pos_end):
        self.statement_nodes = statement_nodes
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return f'[{", ".join(map(str, self.statement_nodes))}]'


class NumberNode:
    def __init__(self, tok):
        self.tok = tok
        self.pos_start = self.tok.pos_start
        self.pos_end = self.tok.pos_end

    def __repr__(self):
        return f"{self.tok}"


class StringNode:
    def __init__(self, tok):
        self.tok = tok
        self.pos_start = self.tok.pos_start
        self.pos_end = self.tok.pos_end

    def __repr__(self):
        return f"{self.tok}"


class ListNode:
    def __init__(self, element_nodes, pos_start, pos_end):
        self.element_nodes = element_nodes
        self.pos_start = pos_start
        self.pos_end = pos_end


class VarAccessNode:
    def __init__(self, var_name_tok):
        self.var_name_tok = var_name_tok
        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.var_name_tok.pos_end


class VarAssignNode:
    def __init__(self, var_name_tok, value_node, is_declaration=False):
        self.var_name_tok = var_name_tok
        self.value_node = value_node
        self.is_declaration = is_declaration
        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.value_node.pos_end


class TernaryOpNode:
    def __init__(self, condition_node, true_case_node, false_case_node):
        self.condition_node = condition_node
        self.true_case_node = true_case_node
        self.false_case_node = false_case_node

        self.pos_start = condition_node.pos_start
        self.pos_end = false_case_node.pos_end

    def __repr__(self):
        return (
            f"({self.condition_node} ? {self.true_case_node} : {self.false_case_node})"
        )


class BinOpNode:
    def __init__(self, left_node, op_tok, right_node):
        self.left_node = left_node
        self.op_tok = op_tok
        self.right_node = right_node
        self.pos_start = self.left_node.pos_start
        self.pos_end = self.right_node.pos_end

    def __repr__(self):
        return f"({self.left_node}, {self.op_tok}, {self.right_node})"


class UnaryOpNode:
    def __init__(self, op_tok, node):
        self.op_tok = op_tok
        self.node = node
        self.pos_start = self.op_tok.pos_start
        self.pos_end = self.node.pos_end

    def __repr__(self):
        return f"({self.op_tok}, {self.node})"


class IfNode:
    def __init__(self, cases, else_case):
        self.cases = cases
        self.else_case = else_case

        self.pos_start = self.cases[0][0].pos_start

        if self.else_case:
            self.pos_end = self.else_case.pos_end
        else:
            self.pos_end = self.cases[len(self.cases) - 1][1].pos_end


class ChainedCompNode:
    def __init__(self, left_node, ops_and_exprs):
        self.left_node = left_node
        self.ops_and_exprs = ops_and_exprs
        self.pos_start = left_node.pos_start
        self.pos_end = ops_and_exprs[-1][1].pos_end

    def __repr__(self):
        return f"({self.left_node}, {self.ops_and_exprs})"


class PrintNode:
    def __init__(self, print_nodes, should_newline=True):
        self.print_nodes = (
            print_nodes if isinstance(print_nodes, list) else [print_nodes]
        )
        self.should_newline = should_newline
        self.pos_start = self.print_nodes[0].pos_start
        self.pos_end = self.print_nodes[-1].pos_end


class FunDefNode:
    def __init__(
        self,
        var_name_tok,
        arg_name_toks,
        body_node,
        visibility="PUBLIC",
        is_static=False,
    ):
        self.var_name_tok = var_name_tok
        self.arg_name_toks = arg_name_toks
        self.body_node = body_node
        self.visibility = visibility
        self.is_static = is_static

        if self.var_name_tok:
            self.pos_start = self.var_name_tok.pos_start
        elif len(self.arg_name_toks) > 0:
            self.pos_start = self.arg_name_toks[0].pos_start
        else:
            self.pos_start = self.body_node.pos_start

        self.pos_end = self.body_node.pos_end


class VisibilityStmtNode:
    def __init__(self, visibility, assign_node, is_final=False):
        self.visibility = visibility
        self.assign_node = assign_node
        self.is_final = is_final
        self.pos_start = assign_node.pos_start
        self.pos_end = assign_node.pos_end


class CallNode:
    def __init__(self, node_to_call, arg_nodes):
        self.node_to_call = node_to_call
        self.arg_nodes = arg_nodes

        self.pos_start = self.node_to_call.pos_start
        if len(self.arg_nodes) > 0:
            self.pos_end = self.arg_nodes[len(self.arg_nodes) - 1].pos_end
        else:
            self.pos_end = self.node_to_call.pos_end


class ReturnNode:
    def __init__(self, node_to_return, pos_start, pos_end):
        self.node_to_return = node_to_return
        self.pos_start = pos_start
        self.pos_end = pos_end


class ClassNode:
    def __init__(
        self, class_name_tok, superclass_nodes, method_nodes, static_field_nodes
    ):
        self.class_name_tok = class_name_tok
        self.superclass_nodes = superclass_nodes
        self.method_nodes = method_nodes
        self.static_field_nodes = static_field_nodes

        self.pos_start = self.class_name_tok.pos_start
        if len(method_nodes) > 0:
            self.pos_end = method_nodes[-1].pos_end
        else:
            self.pos_end = self.class_name_tok.pos_end


class NewInstanceNode:
    def __init__(self, class_name_tok, arg_nodes):
        self.class_name_tok = class_name_tok
        self.arg_nodes = arg_nodes

        self.pos_start = self.class_name_tok.pos_start
        if len(arg_nodes) > 0:
            self.pos_end = arg_nodes[-1].pos_end
        else:
            self.pos_end = self.class_name_tok.pos_end


class GetAttrNode:
    def __init__(self, object_node, attr_name_tok):
        self.object_node = object_node
        self.attr_name_tok = attr_name_tok

        self.pos_start = object_node.pos_start
        self.pos_end = attr_name_tok.pos_end


class SetAttrNode:
    def __init__(self, object_node, attr_name_tok, value_node):
        self.object_node = object_node
        self.attr_name_tok = attr_name_tok
        self.value_node = value_node

        self.pos_start = object_node.pos_start
        self.pos_end = value_node.pos_end


class WhileNode:
    def __init__(self, condition_node, body_node):
        self.condition_node = condition_node
        self.body_node = body_node

        self.pos_start = self.condition_node.pos_start
        self.pos_end = self.body_node.pos_end


class BreakNode:
    def __init__(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end = pos_end


class ContinueNode:
    def __init__(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end = pos_end


class ListAccessNode:
    def __init__(self, list_node, index_node):
        self.list_node = list_node
        self.index_node = index_node

        self.pos_start = list_node.pos_start
        self.pos_end = index_node.pos_end


class ListSetNode:
    def __init__(self, list_node, index_node, value_node):
        self.list_node = list_node
        self.index_node = index_node
        self.value_node = value_node

        self.pos_start = list_node.pos_start
        self.pos_end = value_node.pos_end


class ForNode:
    def __init__(self, var_name_toks, iterable_node, body_node):
        self.var_name_toks = var_name_toks
        self.iterable_node = iterable_node
        self.body_node = body_node

        self.pos_start = self.var_name_toks[0].pos_start
        self.pos_end = self.body_node.pos_end


class PostOpNode:
    def __init__(self, node, op_tok):
        self.node = node
        self.op_tok = op_tok
        self.pos_start = node.pos_start
        self.pos_end = op_tok.pos_end

    def __repr__(self):
        return f"({self.node}, {self.op_tok})"


class DictNode:
    def __init__(self, key_value_pairs, pos_start, pos_end):
        self.key_value_pairs = key_value_pairs
        self.pos_start = pos_start
        self.pos_end = pos_end


class MultiVarAssignNode:
    def __init__(self, var_name_toks, value_node):
        self.var_name_toks = var_name_toks
        self.value_node = value_node
        self.pos_start = var_name_toks[0].pos_start
        self.pos_end = value_node.pos_end


class ListCompNode:
    def __init__(self, output_expr_node, iteration_specs, pos_start, pos_end):
        self.output_expr_node = output_expr_node
        self.iteration_specs = iteration_specs
        self.pos_start = pos_start
        self.pos_end = pos_end


class DictCompNode:
    def __init__(
        self, key_expr_node, value_expr_node, iteration_specs, pos_start, pos_end
    ):
        self.key_expr_node = key_expr_node
        self.value_expr_node = value_expr_node
        self.iteration_specs = iteration_specs
        self.pos_start = pos_start
        self.pos_end = pos_end


class SliceAccessNode:
    def __init__(self, node_to_slice, start_node, end_node):
        self.node_to_slice = node_to_slice
        self.start_node = start_node
        self.end_node = end_node
        self.pos_start = node_to_slice.pos_start
        self.pos_end = end_node.pos_end if end_node else start_node.pos_end


class TryCatchNode:
    def __init__(
        self,
        try_body_node,
        catch_var_node,
        catch_body_node,
        finally_body_node,
        pos_start,
        pos_end,
    ):
        self.try_body_node = try_body_node
        self.catch_var_node = catch_var_node
        self.catch_body_node = catch_body_node
        self.finally_body_node = finally_body_node
        self.pos_start = pos_start
        self.pos_end = pos_end


class ThrowNode:
    def __init__(self, node_to_throw, pos_start, pos_end):
        self.node_to_throw = node_to_throw
        self.pos_start = pos_start
        self.pos_end = pos_end


class FinalVarAssignNode:
    def __init__(self, var_name_tok, value_node):
        self.var_name_tok = var_name_tok
        self.value_node = value_node
        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.value_node.pos_end


class SwitchNode:
    def __init__(self, switch_value_node, cases, default_case):
        self.switch_value_node = switch_value_node
        self.cases = cases
        self.default_case = default_case
        self.pos_start = switch_value_node.pos_start

        if default_case:
            self.pos_end = default_case.pos_end
        elif cases:
            self.pos_end = cases[-1][1].pos_end
        else:
            self.pos_end = switch_value_node.pos_end


class EnumNode:
    def __init__(self, enum_name_tok, cases, pos_start, pos_end):
        self.enum_name_tok = enum_name_tok
        self.cases = cases
        self.pos_start = pos_start
        self.pos_end = pos_end
