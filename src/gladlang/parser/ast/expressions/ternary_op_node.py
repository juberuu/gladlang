"""TernaryOpNode – represents conditional expressions (cond ? true : false)."""


class TernaryOpNode:
    def __init__(self, condition_node, true_case_node, false_case_node):
        self.condition_node = condition_node
        self.true_case_node = true_case_node
        self.false_case_node = false_case_node
        self.pos_start = condition_node.pos_start
        self.pos_end = false_case_node.pos_end

    def __repr__(self):
        return (
            f"({self.condition_node} ? {self.true_case_node} : {self.false_case_node})"
        )
