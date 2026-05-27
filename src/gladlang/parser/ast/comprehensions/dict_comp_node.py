"""DictCompNode – represents dictionary comprehensions {k: v FOR ...}."""


class DictCompNode:
    def __init__(
        self, key_expr_node, value_expr_node, iteration_specs, pos_start, pos_end
    ):
        self.key_expr_node = key_expr_node
        self.value_expr_node = value_expr_node
        self.iteration_specs = iteration_specs
        self.pos_start = pos_start
        self.pos_end = pos_end
