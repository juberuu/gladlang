"""VisibilityStmtNode – wraps assignments with PUBLIC/PRIVATE/PROTECTED/FINAL modifiers."""


class VisibilityStmtNode:
    def __init__(self, visibility, assign_node, is_final=False):
        self.visibility = visibility
        self.assign_node = assign_node
        self.is_final = is_final
        self.pos_start = assign_node.pos_start
        self.pos_end = assign_node.pos_end
