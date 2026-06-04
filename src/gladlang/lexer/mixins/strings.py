"""Double‑quoted and triple‑quoted string lexing with escape sequences."""

from gladlang.core.errors import InvalidSyntaxError
from gladlang.lexer.token import Token
from gladlang.core.constants.token_types import GL_STRING


class LexerStrings:
    def make_string(self):
        chars = []
        pos_start = self.pos.copy()
        is_multiline = False

        self.advance()

        if self.current_char == '"' and self.peek() == '"':
            is_multiline = True
            self.advance()
            self.advance()

        escape_character = False

        while self.current_char is not None:
            if escape_character:
                if self.current_char == "n":
                    chars.append("\n")
                elif self.current_char == "t":
                    chars.append("\t")
                elif self.current_char == "r":
                    chars.append("\r")
                elif self.current_char == '"':
                    chars.append('"')
                elif self.current_char == "\\":
                    chars.append("\\")
                else:
                    chars.append(self.current_char)

                escape_character = False
            elif self.current_char == "\\":
                escape_character = True
            elif self.current_char == '"':
                if is_multiline:
                    if self.peek() == '"':
                        self.advance()
                        if self.peek() == '"':
                            self.advance()
                            break
                        else:
                            chars.append('""')
                    else:
                        chars.append('"')
                else:
                    break
            else:
                chars.append(self.current_char)

            self.advance()

        if self.current_char is None:
            return None, InvalidSyntaxError(
                pos_start, self.pos, "Unterminated string literal"
            )

        string = "".join(chars)
        self.advance()

        return Token(GL_STRING, string, pos_start, self.pos)
