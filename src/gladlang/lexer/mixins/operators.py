"""Two‑character operators: !=, ==, and error handling for '!'."""

from gladlang.core.errors import InvalidSyntaxError
from gladlang.lexer.token import Token
from gladlang.core.constants.token_types import GL_NE, GL_EE, GL_EQ


class LexerOperators:
    def make_not_equals(self):
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == "=":
            self.advance()
            return Token(GL_NE, pos_start=pos_start, pos_end=self.pos), None

        self.advance()

        return None, InvalidSyntaxError(pos_start, self.pos, "Expected '=' after '!'")

    def make_equals(self):
        tok_type = GL_EQ
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == "=":
            self.advance()
            tok_type = GL_EE

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)
