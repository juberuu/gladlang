"""PrintNode – represents PRINT and PRINTLN statements."""


class PrintNode:
    def __init__(self, print_nodes, should_newline=True, pos_start=None, pos_end=None):
        self.print_nodes = (
            print_nodes if isinstance(print_nodes, list) else [print_nodes]
        )

        self.should_newline = should_newline
        if self.print_nodes:
            self.pos_start = self.print_nodes[0].pos_start
            self.pos_end = self.print_nodes[-1].pos_end
        else:
            self.pos_start = pos_start
            self.pos_end = pos_end
