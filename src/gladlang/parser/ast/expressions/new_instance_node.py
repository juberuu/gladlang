"""NewInstanceNode – represents class instantiation (NEW ClassName(...))."""


class NewInstanceNode:
    def __init__(self, class_name_tok, arg_nodes):
        self.class_name_tok = class_name_tok
        self.arg_nodes = arg_nodes
        self.pos_start = self.class_name_tok.pos_start

        if len(arg_nodes) > 0:
            self.pos_end = arg_nodes[-1].pos_end
        else:
            self.pos_end = self.class_name_tok.pos_end
