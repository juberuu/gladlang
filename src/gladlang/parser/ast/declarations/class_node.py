"""ClassNode – represents class definitions with methods and static fields."""


class ClassNode:
    def __init__(
        self, class_name_tok, superclass_nodes, method_nodes, static_field_nodes
    ):
        self.class_name_tok = class_name_tok
        self.superclass_nodes = superclass_nodes
        self.method_nodes = method_nodes
        self.static_field_nodes = static_field_nodes
        self.pos_start = self.class_name_tok.pos_start

        if len(method_nodes) > 0:
            self.pos_end = method_nodes[-1].pos_end
        else:
            self.pos_end = self.class_name_tok.pos_end
