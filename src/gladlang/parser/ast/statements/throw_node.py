"""ThrowNode – represents THROW statements for raising errors."""


class ThrowNode:
    def __init__(self, node_to_throw, pos_start, pos_end):
        self.node_to_throw = node_to_throw
        self.pos_start = pos_start
        self.pos_end = pos_end
