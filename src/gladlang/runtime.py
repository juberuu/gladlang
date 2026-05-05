from threading import Lock


class _NoLock:
    __slots__ = ()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class SymbolTable:
    _THREADING_ENABLED = False

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

            if as_final:
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
        with self._lock:
            value = self.symbols.get(name)
            has_parent = self.parent is not None

        if value is None and has_parent:
            return self.parent.get(name)
        return value

    def update(self, name, value):
        with self._lock:
            if name in self.finals:
                return f"Cannot reassign constant '{name}'"
            if name in self.symbols:
                self.symbols[name] = value
                return None
            has_parent = self.parent is not None

        if has_parent:
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
            new_table.defining_classes = self.defining_classes.copy()
            new_table._finals_count = len(new_table.finals)
            return new_table


class Context:
    __slots__ = (
        "display_name",
        "parent",
        "parent_entry_pos",
        "symbol_table",
        "depth",
        "active_class",
        "is_static",
        "_tco_func",
    )

    def __init__(self, display_name, parent=None, parent_entry_pos=None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos
        self.symbol_table = None
        self.depth = (parent.depth + 1) if parent else 0
        self.active_class = parent.active_class if parent else None
        self.is_static = False


class RTResult:
    __slots__ = (
        "value",
        "error",
        "return_value",
        "should_return",
        "should_break",
        "should_continue",
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.value = None
        self.error = None
        self.return_value = None
        self.should_return = False
        self.should_break = False
        self.should_continue = False

        return self

    def register(self, res):
        if res.error is None and not (
            res.should_return or res.should_break or res.should_continue
        ):
            return res.value

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
