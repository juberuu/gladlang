"""ListSetNode – represents list element assignment (list[index] = value)."""


class ListSetNode:
    def __init__(self, list_node, index_node, value_node):
        self.list_node = list_node
        self.index_node = index_node
        self.value_node = value_node
        self.pos_start = list_node.pos_start
        self.pos_end = value_node.pos_end
