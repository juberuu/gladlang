"""Dict – key-value store with size limit and deep copy semantics."""

from gladlang.core.errors import RTError
from gladlang.core.util.settings import Settings
from gladlang.values.nulls.frozen_null import FrozenNull
from gladlang.values.nulls.mutable_null import MutableNull
from gladlang.values.primitives.number import Number
from gladlang.values.primitives.string import String
from gladlang.values.value import Value


class Dict(Value):
    __slots__ = ("elements", "pos_start", "pos_end", "context")

    def __init__(self, elements):
        self.elements = {}

        for key, value in elements.items():
            self.elements[self._make_key(key)] = value

        self.pos_start = None
        self.pos_end = None
        self.context = None

    def _make_key(self, key):
        if hasattr(key, "_is_null"):
            if key._is_null:
                return ("__null__", key.value)
            else:
                return ("__false__", key.value)

        if isinstance(key, (String, Number)):
            return key.value

        return key

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def is_true(self):
        return len(self.elements) > 0

    def copy(self, _visited=None):
        if _visited is None:
            _visited = {}

        self_id = id(self)
        if self_id in _visited:
            return _visited[self_id]

        new_dict = Dict({})
        _visited[self_id] = new_dict

        from gladlang.values.primitives.list import List

        new_dict.elements = {
            k: (v.copy(_visited) if isinstance(v, (List, Dict)) else v.copy())
            for k, v in self.elements.items()
        }

        new_dict.set_pos(self.pos_start, self.pos_end)
        new_dict.set_context(self.context)
        return new_dict

    def added_to(self, other):
        if isinstance(other, Dict):
            new_len = len(self.elements) + len(other.elements)
            if new_len > Settings.MAX_DICT_SIZE:
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    f"Dict merge result ({new_len}) exceeds maximum allowed size ({Settings.MAX_DICT_SIZE})",
                    self.context,
                )

            from gladlang.values.primitives.list import List

            _visited = {}

            def safe_copy(v):
                if isinstance(v, (List, Dict)):
                    return v.copy(_visited)

                return v.copy()

            merged = {k: safe_copy(v) for k, v in self.elements.items()}
            merged.update({k: safe_copy(v) for k, v in other.elements.items()})

            new_dict = Dict(merged)
            new_dict.set_context(self.context)

            return new_dict, None
        return None, self._illegal(other)

    def get_element_at(self, key):
        if not isinstance(key, (Number, String)):
            return None, RTError(
                self.pos_start,
                self.pos_end,
                "Key must be a Number or String",
                self.context,
            )

        k = self._make_key(key)
        val = self.elements.get(k)
        if val is None:
            return None, RTError(
                self.pos_start,
                self.pos_end,
                f"Key '{key.value}' not found",
                self.context,
            )

        return val, None

    def set_element_at(self, key, value):
        if not isinstance(key, (Number, String)):
            return None, RTError(
                self.pos_start,
                self.pos_end,
                "Key must be a Number or String",
                self.context,
            )

        k = self._make_key(key)
        if k not in self.elements and len(self.elements) >= Settings.MAX_DICT_SIZE:
            return None, RTError(
                self.pos_start,
                self.pos_end,
                f"Dict size limit ({Settings.MAX_DICT_SIZE:,} entries) reached. Cannot insert more keys.",
                self.context,
            )

        self.elements[k] = value
        return value, None

    def get_comparison_eq(self, other, visited=None):
        if isinstance(other, (FrozenNull, MutableNull)):
            return (Number(0).set_context(self.context), None)

        if not isinstance(other, Dict):
            return (None, self._illegal(other))

        if len(self.elements) != len(other.elements):
            return (Number(0).set_context(self.context), None)

        if visited is None:
            visited = set()

        pair = (id(self), id(other))
        if pair in visited:
            return (Number(1).set_context(self.context), None)

        visited.add(pair)

        try:
            for key, value in self.elements.items():
                if key not in other.elements:
                    return (Number(0).set_context(self.context), None)

                result, error = value.get_comparison_eq(other.elements[key], visited)
                if error:
                    return (None, error)

                if not result.is_true():
                    return (Number(0).set_context(self.context), None)
        finally:
            visited.remove(pair)

        return (Number(1).set_context(self.context), None)

    def get_comparison_ne(self, other):
        if isinstance(other, (FrozenNull, MutableNull)):
            return Number(1).set_context(self.context), None

        if not isinstance(other, Dict):
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
            if other.name == "Dict":
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

    def execute(self, args, interpreter=None, calling_context=None):
        from gladlang.runtime.rt_result import RTResult

        return RTResult().failure(self._illegal())

    def get_attr(self, name_tok, context=None):
        return None, self._illegal()

    def set_attr(self, name_tok, value, context=None, visibility=None, as_final=False):
        return None, self._illegal()

    def notted(self):
        return Number(0 if self.is_true() else 1).set_context(self.context), None

    def _illegal(self, other=None):
        if not other:
            other = self

        return RTError(self.pos_start, other.pos_end, "Illegal operation", self.context)

    def illegal_operation(self, other=None):
        return self._illegal(other)

    def __repr__(self):
        return self.to_string([])

    def to_string(self, visited):
        from gladlang.values.primitives.list import List

        if self in visited:
            return "{...}"

        visited.append(self)
        kv_strings = []

        for key, value in self.elements.items():
            if isinstance(value, (List, Dict)):
                val_str = value.to_string(visited)
            elif isinstance(value, String):
                escaped = value.value.replace("\\", "\\\\").replace('"', '\\"')
                val_str = f'"{escaped}"'
            else:
                val_str = repr(value)

            key_str = f'"{key}"' if isinstance(key, str) else repr(key)
            kv_strings.append(f"{key_str}: {val_str}")

        s = f"{{{', '.join(kv_strings)}}}"
        visited.pop()
        return s
