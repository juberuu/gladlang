"""ForNode – represents foreach loops (FOR var IN iterable ...)."""


class ForNode:
    def __init__(self, var_name_toks, iterable_node, body_node):
        self.var_name_toks = var_name_toks
        self.iterable_node = iterable_node
        self.body_node = body_node
        self.pos_start = self.var_name_toks[0].pos_start
        self.pos_end = self.body_node.pos_end
