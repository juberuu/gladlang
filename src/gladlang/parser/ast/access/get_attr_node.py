"""GetAttrNode – represents attribute access (object.attr)."""


class GetAttrNode:
    def __init__(self, object_node, attr_name_tok):
        self.object_node = object_node
        self.attr_name_tok = attr_name_tok
        self.pos_start = object_node.pos_start
        self.pos_end = attr_name_tok.pos_end
