"""Runtime error – includes traceback generation and thrown value support."""

from .error import Error


class RTError(Error):
    MAX_TRACEBACK_FRAMES = 20

    __slots__ = ("context", "thrown_value")

    def __init__(self, pos_start, pos_end, details, context, thrown_value=None):
        super().__init__(pos_start, pos_end, "Runtime Error", details)
        self.context = context
        self.thrown_value = thrown_value

    def as_string(self):
        result = self.generate_traceback()
        result += f"{self.error_name}: {self.details}"

        if self.thrown_value is not None:
            result += f"\nThrown value: {self.thrown_value}"

        return result

    def generate_traceback(self):
        frames = []

        pos = self.pos_start
        ctx = self.context

        visited = set()

        while ctx and id(ctx) not in visited:
            visited.add(id(ctx))

            if pos is not None:
                frames.append(
                    f"  File {pos.fn}, line {pos.ln + 1}, in {ctx.display_name}\n"
                )

            pos = ctx.parent_entry_pos
            ctx = ctx.parent

        if ctx:
            frames.append("  ... cyclic context chain detected ...\n")

        frames.reverse()

        if len(frames) > RTError.MAX_TRACEBACK_FRAMES:
            head = RTError.MAX_TRACEBACK_FRAMES // 2
            tail = RTError.MAX_TRACEBACK_FRAMES - head
            omitted = len(frames) - (head + tail)

            frames = (
                frames[:head]
                + [f"  ... {omitted} frames omitted ...\n"]
                + frames[-tail:]
            )

        if not frames:
            return ""

        return "Traceback (most recent call last):\n" + "".join(frames)
