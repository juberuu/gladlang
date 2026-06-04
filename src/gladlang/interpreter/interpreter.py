"""GladLang AST interpreter and execution engine.

Implements expression evaluation, control flow, function execution,
class handling, and runtime behaviour for all supported language features.
This module is effectively the operational core of the language runtime.
"""

from gladlang.interpreter.mixins import (
    InterpreterBase,
    InterpreterStatements,
    InterpreterExpressions,
    InterpreterLiterals,
    InterpreterVariables,
    InterpreterSlices,
    InterpreterFunctions,
    InterpreterClasses,
    InterpreterEnums,
    InterpreterAttributeAccess,
)


class Interpreter(
    InterpreterBase,
    InterpreterStatements,
    InterpreterExpressions,
    InterpreterLiterals,
    InterpreterVariables,
    InterpreterSlices,
    InterpreterFunctions,
    InterpreterClasses,
    InterpreterEnums,
    InterpreterAttributeAccess,
):
    pass
