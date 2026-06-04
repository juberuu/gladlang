"""GladLang lexical analyzer.

Transforms raw source code into a structured stream of tokens consumed
by the parser. Supports literals, identifiers, operators, comments,
escape sequences, and multiple numeric formats.
"""

from gladlang.lexer.mixins import (
    LexerBase,
    LexerNumbers,
    LexerIdentifiers,
    LexerStrings,
    LexerTemplate,
    LexerOperators,
    LexerPunctuation,
)


class Lexer(
    LexerBase,
    LexerNumbers,
    LexerIdentifiers,
    LexerStrings,
    LexerTemplate,
    LexerOperators,
    LexerPunctuation,
):
    pass
