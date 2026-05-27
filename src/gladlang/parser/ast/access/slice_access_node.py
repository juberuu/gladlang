"""SliceAccessNode – represents slicing (list[start:end] or string[start:end])."""


class SliceAccessNode:
    def __init__(self, node_to_slice, start_node, end_node):
        self.node_to_slice = node_to_slice
        self.start_node = start_node
        self.end_node = end_node
        self.pos_start = node_to_slice.pos_start

        if end_node is not None:
            self.pos_end = end_node.pos_end
        elif start_node is not None:
            self.pos_end = start_node.pos_end
        else:
            self.pos_end = node_to_slice.pos_end
