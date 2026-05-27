"""TryCatchNode – represents TRY / CATCH / FINALLY exception handling blocks."""


class TryCatchNode:
    def __init__(
        self,
        try_body_node,
        catch_var_node,
        catch_body_node,
        finally_body_node,
        pos_start,
        pos_end,
    ):
        self.try_body_node = try_body_node
        self.catch_var_node = catch_var_node
        self.catch_body_node = catch_body_node
        self.finally_body_node = finally_body_node
        self.pos_start = pos_start
        self.pos_end = pos_end
