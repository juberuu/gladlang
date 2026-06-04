"""Runtime error – includes traceback generation and thrown value support."""

from .error import Error


class RTError(Error):
    def __init__(self, pos_start, pos_end, details, context, thrown_value=None):
        super().__init__(pos_start, pos_end, "Runtime Error", details)
        self.context = context
        self.thrown_value = thrown_value

    def as_string(self):
        result = self.generate_traceback()
        result += f"{self.error_name}: {self.details}"
        return result

    def generate_traceback(self):
        result = ""
        pos = self.pos_start
        ctx = self.context

        while ctx:
            if pos is not None:
                result = (
                    f"  File {pos.fn}, line {str(pos.ln + 1)}, in {ctx.display_name}\n"
                    + result
                )

            pos = ctx.parent_entry_pos
            ctx = ctx.parent

        return "Traceback (most recent call last):\n" + result
