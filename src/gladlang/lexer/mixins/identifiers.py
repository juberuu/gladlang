"""Identifier and keyword lexing."""

from gladlang.core.constants import KEYWORDS
from gladlang.lexer.token import Token
from gladlang.core.constants.token_types import GL_KEYWORD, GL_IDENTIFIER


class LexerIdentifiers:
    def make_identifier(self):
        id_str = ""
        pos_start = self.pos.copy()

        while (
            self.current_char is not None
            and (id_str + self.current_char).isidentifier()
        ):
            id_str += self.current_char
            self.advance()

        tok_type = GL_KEYWORD if id_str in KEYWORDS else GL_IDENTIFIER

        return Token(tok_type, id_str, pos_start, self.pos)
