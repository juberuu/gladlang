"""ListCompNode – represents list comprehensions [expr FOR ...]."""


class ListCompNode:
    def __init__(self, output_expr_node, iteration_specs, pos_start, pos_end):
        self.output_expr_node = output_expr_node
        self.iteration_specs = iteration_specs
        self.pos_start = pos_start
        self.pos_end = pos_end
