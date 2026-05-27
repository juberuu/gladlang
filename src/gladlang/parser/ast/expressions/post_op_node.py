"""PostOpNode – represents post-increment/decrement (i++, i--)."""


class PostOpNode:
    def __init__(self, node, op_tok):
        self.node = node
        self.op_tok = op_tok
        self.pos_start = node.pos_start
        self.pos_end = op_tok.pos_end

    def __repr__(self):
        return f"({self.node}, {self.op_tok})"
