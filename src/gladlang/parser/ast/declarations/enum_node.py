"""EnumNode – represents enum definitions with named cases."""


class EnumNode:
    def __init__(self, enum_name_tok, cases, pos_start, pos_end):
        self.enum_name_tok = enum_name_tok
        self.cases = cases
        self.pos_start = pos_start
        self.pos_end = pos_end
