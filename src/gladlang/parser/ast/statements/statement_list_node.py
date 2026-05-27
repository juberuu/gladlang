"""StatementListNode – represents a sequence of statements (a block)."""


class StatementListNode:
    def __init__(self, statement_nodes, pos_start, pos_end):
        self.statement_nodes = statement_nodes
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return f'[{", ".join(map(str, self.statement_nodes))}]'
