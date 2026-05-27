"""SwitchNode – represents SWITCH / CASE / DEFAULT statements."""


class SwitchNode:
    def __init__(self, switch_value_node, cases, default_case):
        self.switch_value_node = switch_value_node
        self.cases = cases
        self.default_case = default_case
        self.pos_start = switch_value_node.pos_start

        if default_case:
            self.pos_end = default_case.pos_end
        elif cases:
            self.pos_end = cases[-1][1].pos_end
        else:
            self.pos_end = switch_value_node.pos_end
