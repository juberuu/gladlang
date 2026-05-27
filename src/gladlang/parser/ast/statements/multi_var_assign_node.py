"""MultiVarAssignNode – represents destructuring assignment (LET [x, y] = list)."""


class MultiVarAssignNode:
    def __init__(self, var_name_toks, value_node):
        self.var_name_toks = var_name_toks
        self.value_node = value_node
        self.pos_start = var_name_toks[0].pos_start
        self.pos_end = value_node.pos_end
