"""PrintNode – represents PRINT and PRINTLN statements."""


class PrintNode:
    def __init__(self, print_nodes, should_newline=True):
        self.print_nodes = (
            print_nodes if isinstance(print_nodes, list) else [print_nodes]
        )

        self.should_newline = should_newline
        self.pos_start = self.print_nodes[0].pos_start
        self.pos_end = self.print_nodes[-1].pos_end
