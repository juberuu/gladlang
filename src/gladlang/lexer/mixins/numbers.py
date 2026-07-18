"""Number lexing (integers, floats, hex, octal, binary)."""

from gladlang.core.constants import DIGITS
from gladlang.core.errors import IllegalCharError, InvalidSyntaxError
from gladlang.lexer.token import Token
from gladlang.core.constants.token_types import GL_INT, GL_FLOAT


class LexerNumbers:
    def make_number(self):
        num_str = ""
        dot_count = 0
        pos_start = self.pos.copy()
        has_exponent = False

        def collect_digits(valid_chars):
            nonlocal num_str
            while self.current_char is not None:
                if self.current_char == "_":
                    self.advance()
                    continue

                if self.current_char in valid_chars:
                    num_str += self.current_char
                    self.advance()
                else:
                    break

        if self.current_char == "0":
            peek_char = self.peek()

            if peek_char in ("x", "X"):
                self.advance()
                self.advance()
                collect_digits(DIGITS + "abcdefABCDEF")

                if not num_str:
                    return None, IllegalCharError(
                        pos_start, self.pos, "Invalid hex literal"
                    )

                return Token(GL_INT, int(num_str, 16), pos_start, self.pos), None

            elif peek_char in ("o", "O"):
                self.advance()
                self.advance()
                collect_digits("01234567")

                if not num_str:
                    return None, IllegalCharError(
                        pos_start, self.pos, "Invalid octal literal"
                    )

                return Token(GL_INT, int(num_str, 8), pos_start, self.pos), None

            elif peek_char in ("b", "B"):
                self.advance()
                self.advance()
                collect_digits("01")

                if not num_str:
                    return None, IllegalCharError(
                        pos_start, self.pos, "Invalid binary literal"
                    )

                return Token(GL_INT, int(num_str, 2), pos_start, self.pos), None

        while self.current_char is not None and self.current_char in DIGITS + "._":
            if self.current_char == "_":
                self.advance()
                if self.current_char is None or self.current_char not in DIGITS + ".":
                    return None, InvalidSyntaxError(
                        pos_start,
                        self.pos,
                        "Invalid numeric literal: '_' must be between digits",
                    )

                continue

            if self.current_char == ".":
                if dot_count == 1:
                    break

                if has_exponent:
                    return None, InvalidSyntaxError(
                        pos_start,
                        self.pos,
                        "Invalid numeric literal: '.' after exponent",
                    )

                dot_count += 1
                num_str += "."
            else:
                num_str += self.current_char
            self.advance()

        if self.current_char in ("e", "E"):
            has_exponent = True
            num_str += self.current_char
            self.advance()
            if self.current_char in ("+", "-"):
                num_str += self.current_char
                self.advance()

            if self.current_char is None or self.current_char not in DIGITS:
                return None, InvalidSyntaxError(
                    pos_start,
                    self.pos,
                    "Invalid scientific notation: expected digits after exponent",
                )

            while self.current_char is not None and self.current_char in DIGITS:
                num_str += self.current_char
                self.advance()

            return Token(GL_FLOAT, float(num_str), pos_start, self.pos), None

        num_str = num_str.replace("_", "")

        if dot_count == 0:
            return Token(GL_INT, int(num_str), pos_start, self.pos), None
        else:
            return Token(GL_FLOAT, float(num_str), pos_start, self.pos), None
