"""Number lexing (integers, floats, hex, octal, binary)."""

from gladlang.core.constants import DIGITS
from gladlang.core.errors import IllegalCharError
from gladlang.lexer.token import Token
from gladlang.core.constants.token_types import GL_INT, GL_FLOAT


class LexerNumbers:
    def make_number(self):
        num_str = ""
        dot_count = 0
        pos_start = self.pos.copy()

        if self.current_char == "0":
            peek_char = self.peek()

            if peek_char in ("x", "X"):
                self.advance()
                self.advance()

                if self.current_char is None or not (
                    self.current_char in DIGITS or self.current_char.lower() in "abcdef"
                ):
                    return Token(GL_INT, 0, pos_start, self.pos), IllegalCharError(
                        pos_start, self.pos, "Invalid hex literal"
                    )

                while self.current_char is not None and (
                    self.current_char in DIGITS or self.current_char.lower() in "abcdef"
                ):
                    num_str += self.current_char
                    self.advance()

                return Token(GL_INT, int(num_str, 16), pos_start, self.pos)

            elif peek_char in ("o", "O"):
                self.advance()
                self.advance()

                if self.current_char is None or self.current_char not in "01234567":
                    return Token(GL_INT, 0, pos_start, self.pos), IllegalCharError(
                        pos_start, self.pos, "Invalid octal literal"
                    )

                while self.current_char is not None and self.current_char in "01234567":
                    num_str += self.current_char
                    self.advance()

                return Token(GL_INT, int(num_str, 8), pos_start, self.pos)

            elif peek_char in ("b", "B"):
                self.advance()
                self.advance()

                if self.current_char is None or self.current_char not in "01":
                    return Token(GL_INT, 0, pos_start, self.pos), IllegalCharError(
                        pos_start, self.pos, "Invalid binary literal"
                    )

                while self.current_char is not None and self.current_char in "01":
                    num_str += self.current_char
                    self.advance()

                return Token(GL_INT, int(num_str, 2), pos_start, self.pos)

        while self.current_char is not None and self.current_char in DIGITS + ".":
            if self.current_char == ".":
                if dot_count == 1:
                    break

                dot_count += 1
                num_str += "."
            else:
                num_str += self.current_char
            self.advance()

        if dot_count == 0:
            return Token(GL_INT, int(num_str), pos_start, self.pos)
        else:
            return Token(GL_FLOAT, float(num_str), pos_start, self.pos)
