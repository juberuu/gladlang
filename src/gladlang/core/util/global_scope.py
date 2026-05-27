"""Fresh global scope factory – initialises a new symbol table with built-in values."""


def get_fresh_global_scope():
    from gladlang.runtime.symbol_table import SymbolTable
    from gladlang.values.primitives.number import Number
    from gladlang.values.functions.built_in_function import BuiltInFunction
    from gladlang.values.classes.type_ import Type

    scope = SymbolTable()

    scope.set("NULL", Number.null.copy())
    scope.set("FALSE", Number.false.copy())
    scope.set("TRUE", Number.true.copy())

    scope.set("Number", Type("Number"))
    scope.set("String", Type("String"))
    scope.set("List", Type("List"))
    scope.set("Dict", Type("Dict"))
    scope.set("Enum", Type("Enum"))
    scope.set("Function", Type("Function"))
    scope.set("Object", Type("Object"))

    scope.set("INPUT", BuiltInFunction("INPUT"))
    scope.set("STR", BuiltInFunction("STR"))
    scope.set("INT", BuiltInFunction("INT"))
    scope.set("FLOAT", BuiltInFunction("FLOAT"))
    scope.set("BOOL", BuiltInFunction("BOOL"))

    scope.set("LEN", BuiltInFunction("LEN"))
    scope.set("LENGTH", BuiltInFunction("LEN"))

    return scope
