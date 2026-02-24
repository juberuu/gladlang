from .errors import RTError
import threading
from threading import Lock


class ThreadSafeContext:
    _storage = threading.local()

    @classmethod
    def get_current(cls):
        return getattr(cls._storage, "context", None)

    @classmethod
    def set_current(cls, context):
        cls._storage.context = context


class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent
        self.finals = set()
        self.visibilities = {}
        self._lock = Lock()

    def set(self, name, value, visibility="PUBLIC", as_final=False):
        with self._lock:
            self.symbols[name] = value
            self.visibilities[name] = visibility
            if as_final:
                self.finals.add(name)

    def set_if_absent(self, name, value, visibility="PUBLIC", as_final=False):
        with self._lock:
            if name in self.symbols:
                return f"Variable '{name}' is already defined"
            self.symbols[name] = value
            self.visibilities[name] = visibility
            if as_final:
                self.finals.add(name)
            return None

    def get(self, name):
        with self._lock:
            value = self.symbols.get(name)
            if value is None and self.parent:
                return self.parent.get(name)
            return value

    def update(self, name, value):
        with self._lock:
            if name in self.finals:
                return f"Cannot reassign constant '{name}'"
            if name in self.symbols:
                self.symbols[name] = value
                return None
            if self.parent:
                return self.parent.update(name, value)
            return f"'{name}' is not defined"

    def remove(self, name):
        with self._lock:
            if name in self.symbols:
                del self.symbols[name]
            if name in self.finals:
                self.finals.remove(name)

    def get_visibility(self, name):
        with self._lock:
            return self.visibilities.get(name, "PUBLIC")

    def copy(self):
        with self._lock:
            new_table = SymbolTable(self.parent)
            new_table.symbols = self.symbols.copy()
            new_table.visibilities = self.visibilities.copy()
            new_table.finals = self.finals.copy()
            return new_table


class Context:
    def __init__(self, display_name, parent=None, parent_entry_pos=None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos
        self.symbol_table = None
        self.depth = (parent.depth + 1) if parent else 0
        self.active_class = parent.active_class if parent else None


class RTResult:
    def __init__(self):
        self.value = None
        self.error = None
        self.return_value = None
        self.should_return = False
        self.should_break = False
        self.should_continue = False

    def register(self, res):
        if res.error:
            self.error = res.error
        if res.should_return:
            self.return_value = res.return_value
            self.should_return = True
        if res.should_break:
            self.should_break = True
        if res.should_continue:
            self.should_continue = True
        return res.value

    def success(self, value):
        self.value = value
        return self

    def success_return(self, value):
        self.return_value = value
        self.should_return = True
        return self

    def success_break(self):
        self.should_break = True
        return self

    def success_continue(self):
        self.should_continue = True
        return self

    def failure(self, error):
        self.error = error
        return self
