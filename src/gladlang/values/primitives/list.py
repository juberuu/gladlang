"""List – ordered collection with concatenation, repetition, indexing, and size limit."""

from gladlang.core.errors import RTError
from gladlang.values.primitives.number import Number
from gladlang.values.value import Value


class List(Value):
    MAX_LIST_SIZE = 1_000_000

    __slots__ = ("elements", "pos_start", "pos_end", "context")

    def __init__(self, elements):
        self.elements = elements
        self.pos_start = None
        self.pos_end = None
        self.context = None

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def is_true(self):
        return len(self.elements) > 0

    def added_to(self, other):
        if isinstance(other, List):
            new_len = len(self.elements) + len(other.elements)
            if new_len > List.MAX_LIST_SIZE:
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    f"List concatenation result ({new_len}) exceeds maximum allowed size ({List.MAX_LIST_SIZE})",
                    self.context,
                )

            new_list = List(self.elements + other.elements)
            new_list.set_context(self.context)

            return new_list, None
        return None, self._illegal(other)

    def multed_by(self, other):
        if isinstance(other, Number):
            multiplier_raw = other.value
            if isinstance(multiplier_raw, float) and not multiplier_raw.is_integer():
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    f"List repetition count must be a whole number, got {multiplier_raw}",
                    self.context,
                )

            multiplier = int(multiplier_raw)
            if multiplier < 0:
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    "List repetition count cannot be negative",
                    self.context,
                )

            result_len = len(self.elements) * multiplier
            if result_len > List.MAX_LIST_SIZE:
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    f"List repetition result ({result_len}) exceeds maximum allowed size ({List.MAX_LIST_SIZE})",
                    self.context,
                )

            new_list = List(self.elements * multiplier)
            new_list.set_context(self.context)

            return new_list, None
        return None, self._illegal(other)

    def get_element_at(self, index):
        if not isinstance(index, Number):
            return None, RTError(
                self.pos_start,
                self.pos_end,
                "List index must be a Number",
                self.context,
            )

        try:
            return self.elements[int(index.value)], None
        except IndexError:
            return None, RTError(
                self.pos_start,
                self.pos_end,
                f"List index {index.value} out of bounds",
                self.context,
            )

    def set_element_at(self, index, value):
        if not isinstance(index, Number):
            return None, RTError(
                self.pos_start,
                self.pos_end,
                "List index must be a Number",
                self.context,
            )

        try:
            self.elements[int(index.value)] = value
            return value, None
        except IndexError:
            return None, RTError(
                self.pos_start,
                self.pos_end,
                f"List index {index.value} out of bounds",
                self.context,
            )

    def get_comparison_eq(self, other, visited=None):
        if not isinstance(other, List):
            return None, self._illegal(other)

        if len(self.elements) != len(other.elements):
            return Number(0).set_context(self.context), None

        if visited is None:
            visited = set()

        pair = (id(self), id(other))
        if pair in visited:
            return Number(1).set_context(self.context), None

        visited.add(pair)

        try:
            for i in range(len(self.elements)):
                result, error = self.elements[i].get_comparison_eq(
                    other.elements[i], visited
                )

                if error:
                    return None, error

                if not result.is_true():
                    return Number(0).set_context(self.context), None

        finally:
            visited.remove(pair)

        return Number(1).set_context(self.context), None

    def get_comparison_ne(self, other):
        if not isinstance(other, List):
            return None, self._illegal(other)

        result, error = self.get_comparison_eq(other)
        if error:
            return None, error

        return (Number(0) if result.is_true() else Number(1)).set_context(
            self.context
        ), None

    def get_comparison_is(self, other):
        return Number(1 if self is other else 0).set_context(self.context), None

    def get_comparison_instanceof(self, other):
        from gladlang.values.classes.type_ import Type
        from gladlang.values.classes.class_ import Class

        if isinstance(other, Type):
            if other.name == "List":
                return Number.true.copy(), None

            if other.name == "Object":
                return Number.true.copy(), None

            return Number.false.copy(), None

        if isinstance(other, Class):
            return Number.false.copy(), None

        return None, RTError(
            self.pos_start,
            self.pos_end,
            "Right operand of INSTANCEOF must be a Class or Type",
            self.context,
        )

    def anded_by(self, other):
        return (
            Number(1 if (self.is_true() and other.is_true()) else 0).set_context(
                self.context
            ),
            None,
        )

    def ored_by(self, other):
        return (
            Number(1 if (self.is_true() or other.is_true()) else 0).set_context(
                self.context
            ),
            None,
        )

    def copy(self, _visited=None):
        from gladlang.values.primitives.dict import Dict

        if _visited is None:
            _visited = {}

        self_id = id(self)
        if self_id in _visited:
            return _visited[self_id]

        new_list = List([])
        _visited[self_id] = new_list

        new_list.elements = [
            e.copy(_visited) if isinstance(e, (List, Dict)) else e.copy()
            for e in self.elements
        ]

        new_list.set_pos(self.pos_start, self.pos_end)
        new_list.set_context(self.context)
        return new_list

    def execute(self, args, interpreter=None):
        from gladlang.runtime.rt_result import RTResult

        return RTResult().failure(self._illegal())

    def get_attr(self, name_tok, context=None):
        return None, self._illegal()

    def set_attr(self, name_tok, value, context=None, visibility=None, as_final=False):
        return None, self._illegal()

    def notted(self):
        return None, self._illegal()

    def _illegal(self, other=None):
        if not other:
            other = self

        return RTError(self.pos_start, other.pos_end, "Illegal operation", self.context)

    def illegal_operation(self, other=None):
        return self._illegal(other)

    def __repr__(self):
        return self.to_string([])

    def to_string(self, visited):
        from gladlang.values.primitives.dict import Dict

        if self in visited:
            return "[...]"

        visited.append(self)

        s = f'[{", ".join([x.to_string(visited) if isinstance(x, (List, Dict)) else repr(x) for x in self.elements])}]'

        visited.pop()
        return s
