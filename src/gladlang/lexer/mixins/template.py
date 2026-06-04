"""Backtick template string lexing (interpolation)."""

from gladlang.lexer.token import Token
from gladlang.core.constants.token_types import (
    GL_STRING,
    GL_LPAREN,
    GL_RPAREN,
    GL_PLUS,
    GL_IDENTIFIER,
    GL_EOF,
)


class LexerTemplate:
    def make_template_string(self):
        from gladlang.lexer.lexer import Lexer

        tokens = []
        pos_start = self.pos.copy()
        self.advance()

        tokens.append(Token(GL_LPAREN, pos_start=pos_start))

        chars = []
        escape_character = False

        while self.current_char is not None and (
            self.current_char != "`" or escape_character
        ):
            if not escape_character and self.current_char == "$" and self.peek() == "{":
                string_part = "".join(chars)
                tokens.append(Token(GL_STRING, string_part, pos_start=pos_start))
                chars = []

                tokens.append(Token(GL_PLUS, pos_start=self.pos))
                tokens.append(Token(GL_IDENTIFIER, "STR", pos_start=self.pos))
                tokens.append(Token(GL_LPAREN, pos_start=self.pos))

                self.advance()
                self.advance()

                expr_str = ""
                brace_count = 1
                in_inner_string = False
                escape_next = False

                while self.current_char is not None and brace_count > 0:
                    ch = self.current_char

                    if escape_next:
                        expr_str += ch
                        escape_next = False
                    elif ch == "\\" and in_inner_string:
                        expr_str += ch
                        escape_next = True
                    elif ch == '"':
                        in_inner_string = not in_inner_string
                        expr_str += ch
                    elif not in_inner_string:
                        if ch == "{":
                            brace_count += 1
                        elif ch == "}":
                            brace_count -= 1

                        if brace_count > 0:
                            expr_str += ch

                    else:
                        expr_str += ch

                    self.advance()

                interp_start_idx = self.pos.idx - len(expr_str) - 2
                interp_start_ln = self.pos.ln
                col = self.pos.col

                for ch in expr_str:
                    if ch == "\n":
                        col = 0
                    else:
                        col -= 1

                interp_start_col = max(0, col - 2)

                sub_lexer = Lexer(self.fn, expr_str)

                sub_tokens, error = sub_lexer.make_tokens()

                if error:
                    if error.pos_start is not None:
                        error.pos_start.idx += interp_start_idx
                        error.pos_start.col += interp_start_col

                        if error.pos_start.ln == 0:
                            error.pos_start.ln = interp_start_ln

                        error.pos_end = error.pos_start.copy()

                    return [], error

                if sub_tokens and sub_tokens[-1].type == GL_EOF:
                    sub_tokens.pop()

                tokens.extend(sub_tokens)

                tokens.append(Token(GL_RPAREN, pos_start=self.pos))
                tokens.append(Token(GL_PLUS, pos_start=self.pos))

            elif escape_character:
                if self.current_char == "n":
                    chars.append("\n")
                elif self.current_char == "t":
                    chars.append("\t")
                elif self.current_char == "r":
                    chars.append("\r")
                elif self.current_char == "`":
                    chars.append("`")
                elif self.current_char == "\\":
                    chars.append("\\")
                elif self.current_char == '"':
                    chars.append('"')
                elif self.current_char == "'":
                    chars.append("'")
                elif self.current_char == "$":
                    chars.append("$")
                else:
                    chars.append(self.current_char)

                escape_character = False
                self.advance()

            elif self.current_char == "\\":
                escape_character = True
                self.advance()

            else:
                chars.append(self.current_char)
                self.advance()

        string_part = "".join(chars)

        tokens.append(Token(GL_STRING, string_part, pos_start=pos_start))
        tokens.append(Token(GL_RPAREN, pos_start=self.pos))

        self.advance()

        return tokens
