"""GladLang parser implementation.

Consumes token streams produced by the lexer and constructs the
corresponding Abstract Syntax Tree while enforcing grammar rules,
operator precedence, and syntactic validity.
"""

from gladlang.parser.mixins import (
    ParserBase,
    ParserStatements,
    ParserExpressions,
    ParserOperators,
    ParserClasses,
    ParserFunctions,
    ParserEnums,
    ParserCollections,
    ParserControlFlow,
)


class Parser(
    ParserBase,
    ParserStatements,
    ParserExpressions,
    ParserOperators,
    ParserClasses,
    ParserFunctions,
    ParserEnums,
    ParserCollections,
    ParserControlFlow,
):
    pass