"""SetAttrNode – represents attribute assignment (object.attr = value)."""


class SetAttrNode:
    def __init__(self, object_node, attr_name_tok, value_node):
        self.object_node = object_node
        self.attr_name_tok = attr_name_tok
        self.value_node = value_node
        self.pos_start = object_node.pos_start
        self.pos_end = value_node.pos_end
