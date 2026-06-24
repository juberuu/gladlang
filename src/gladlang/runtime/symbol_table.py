"""SymbolTable – manages variable scopes, constants, visibility, and thread-safe access."""

from threading import Lock
from gladlang.core.util.locking import _NoLock


class SymbolTable:
    _THREADING_ENABLED = True

    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent
        self.finals = set()
        self.visibilities = {}
        self.defining_classes = {}
        self._lock = Lock() if SymbolTable._THREADING_ENABLED else _NoLock()
        self._finals_count = 0

    def set(
        self, name, value, visibility="PUBLIC", as_final=False, defining_class=None
    ):
        with self._lock:
            self.symbols[name] = value
            if visibility != "PUBLIC":
                self.visibilities[name] = visibility
            else:
                self.visibilities.pop(name, None)

            if as_final:
                if name not in self.finals:
                    self.finals.add(name)
                    self._finals_count += 1

            if defining_class:
                self.defining_classes[name] = defining_class

    def is_final_in_ancestors(self, name):
        current = self.parent
        while current:
            with current._lock:
                if name in current.finals:
                    return True

            current = current.parent
        return False

    def set_if_absent(self, name, value, visibility="PUBLIC", as_final=False):
        with self._lock:
            if name in self.symbols:
                return f"Variable '{name}' is already defined"

            if as_final and self.is_final_in_ancestors(name):
                return f"Cannot declare constant '{name}' because it is already defined as constant in outer scope"

            self.symbols[name] = value
            if visibility != "PUBLIC":
                self.visibilities[name] = visibility

            if as_final:
                self.finals.add(name)
                self._finals_count += 1

            return None

    def get(self, name):
        current = self
        while current is not None:
            with current._lock:
                value = current.symbols.get(name)
                if value is not None:
                    return value

                parent = current.parent

            current = parent

        return None

    def update(self, name, value):
        current = self
        while current is not None:
            with current._lock:
                if name in current.finals:
                    return f"Cannot reassign constant '{name}'"

                if name in current.symbols:
                    current.symbols[name] = value
                    return None

                parent = current.parent

            current = parent

        return f"'{name}' is not defined"

    def remove(self, name):
        with self._lock:
            self.symbols.pop(name, None)
            if name in self.finals:
                self.finals.discard(name)
                self._finals_count = max(0, self._finals_count - 1)

            self.visibilities.pop(name, None)
            self.defining_classes.pop(name, None)

    def get_visibility(self, name):
        with self._lock:
            return self.visibilities.get(name, "PUBLIC")

    def copy(self):
        with self._lock:
            new_table = SymbolTable(self.parent)
            new_table.symbols = self.symbols.copy()
            new_table.visibilities = self.visibilities.copy()
            new_table.finals = self.finals.copy()
            new_table.defining_classes = self.defining_classes.copy()
            new_table._finals_count = len(new_table.finals)

            return new_table
