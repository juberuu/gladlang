from .errors import RTError


class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.finals = []
        self.parent = parent

    def get(self, name):
        value = self.symbols.get(name, None)
        if value == None and self.parent:
            return self.parent.get(name)
        return value

    def set(self, name, value, as_final=False):
        self.symbols[name] = value
        if as_final:
            self.finals.append(name)

    def remove(self, name):
        del self.symbols[name]
        if name in self.finals:
            self.finals.remove(name)

    def update(self, name, value):
        if name in self.symbols:
            if name in self.finals:
                return f"Cannot reassign constant '{name}'"

            self.symbols[name] = value
            return None

        if self.parent:
            return self.parent.update(name, value)

        return f"'{name}' is not defined"


class Context:
    def __init__(self, display_name, parent=None, parent_entry_pos=None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos
        self.symbol_table = None


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
