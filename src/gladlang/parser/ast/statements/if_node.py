"""IfNode – represents IF / ELSE IF / ELSE conditional branches."""


class IfNode:
    def __init__(self, cases, else_case):
        self.cases = cases
        self.else_case = else_case
        self.pos_start = self.cases[0][0].pos_start

        if self.else_case:
            self.pos_end = self.else_case.pos_end
        else:
            self.pos_end = self.cases[len(self.cases) - 1][1].pos_end
