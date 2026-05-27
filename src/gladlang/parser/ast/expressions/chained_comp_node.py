"""ChainedCompNode – represents chained comparisons (e.g., 1 < x < 10)."""


class ChainedCompNode:
    def __init__(self, left_node, ops_and_exprs):
        self.left_node = left_node
        self.ops_and_exprs = ops_and_exprs
        self.pos_start = left_node.pos_start
        self.pos_end = ops_and_exprs[-1][1].pos_end

    def __repr__(self):
        return f"({self.left_node}, {self.ops_and_exprs})"
