"""Core lexer state, position management, comment skipping, and main token loop."""

from gladlang.core.constants import DIGITS
from gladlang.core.errors import Position, IllegalCharError
from gladlang.lexer.token import Token
from gladlang.core.constants.token_types import (
    GL_PLUS,
    GL_PLUSPLUS,
    GL_PLUSEQ,
    GL_MINUS,
    GL_MINUSMINUS,
    GL_MINUSEQ,
    GL_MUL,
    GL_POW,
    GL_MULEQ,
    GL_POWEQ,
    GL_DIV,
    GL_FLOORDIV,
    GL_DIVEQ,
    GL_FLOORDIVEQ,
    GL_MOD,
    GL_MODEQ,
    GL_BIT_AND,
    GL_BIT_ANDEQ,
    GL_BIT_OR,
    GL_BIT_OREQ,
    GL_BIT_XOR,
    GL_BIT_XOREQ,
    GL_BIT_NOT,
    GL_LSHIFT,
    GL_LSHIFTEQ,
    GL_RSHIFT,
    GL_RSHIFTEQ,
    GL_LT,
    GL_LTE,
    GL_GT,
    GL_GTE,
    GL_LPAREN,
    GL_RPAREN,
    GL_LBRACE,
    GL_RBRACE,
    GL_LSQUARE,
    GL_RSQUARE,
    GL_COMMA,
    GL_DOT,
    GL_COLON,
    GL_SEMI,
    GL_QMARK,
    GL_EOF,
)


class LexerBase:
    def __init__(self, fn, text):
        self.fn = fn
        self.text = text
        self.pos = Position(-1, 0, -1, fn, text)
        self.current_char = None
        self.advance()

    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = (
            self.text[self.pos.idx] if self.pos.idx < len(self.text) else None
        )

    def peek(self):
        peek_pos = self.pos.idx + 1
        if peek_pos < len(self.text):
            return self.text[peek_pos]

        return None

    def skip_comment(self):
        self.advance()
        while self.current_char != "\n" and self.current_char is not None:
            self.advance()

    def make_tokens(self):
        tokens = []
        while self.current_char is not None:
            if self.current_char in " \t\r\n":
                self.advance()
            elif self.current_char == "#":
                self.skip_comment()
            elif self.current_char in DIGITS:
                tok = self.make_number()
                if isinstance(tok, tuple):
                    return [], tok[1]

                tokens.append(tok)
            elif self.current_char.isidentifier():
                tokens.append(self.make_identifier())
            elif self.current_char == '"':
                tok = self.make_string()
                if isinstance(tok, tuple):
                    return [], tok[1]

                tokens.append(tok)
            elif self.current_char == "+":
                pos_start = self.pos.copy()
                self.advance()
                if self.current_char == "+":
                    tokens.append(
                        Token(GL_PLUSPLUS, pos_start=pos_start, pos_end=self.pos)
                    )
                    self.advance()
                elif self.current_char == "=":
                    tokens.append(
                        Token(GL_PLUSEQ, pos_start=pos_start, pos_end=self.pos)
                    )
                    self.advance()
                else:
                    tokens.append(Token(GL_PLUS, pos_start=pos_start))
            elif self.current_char == "-":
                pos_start = self.pos.copy()
                self.advance()
                if self.current_char == "-":
                    tokens.append(
                        Token(GL_MINUSMINUS, pos_start=pos_start, pos_end=self.pos)
                    )
                    self.advance()
                elif self.current_char == "=":
                    tokens.append(
                        Token(GL_MINUSEQ, pos_start=pos_start, pos_end=self.pos)
                    )
                    self.advance()
                else:
                    tokens.append(Token(GL_MINUS, pos_start=pos_start))
            elif self.current_char == "*":
                pos_start = self.pos.copy()
                self.advance()
                if self.current_char == "*":
                    self.advance()
                    if self.current_char == "=":
                        tokens.append(
                            Token(GL_POWEQ, pos_start=pos_start, pos_end=self.pos)
                        )
                        self.advance()
                    else:
                        tokens.append(
                            Token(GL_POW, pos_start=pos_start, pos_end=self.pos)
                        )
                elif self.current_char == "=":
                    tokens.append(
                        Token(GL_MULEQ, pos_start=pos_start, pos_end=self.pos)
                    )
                    self.advance()
                else:
                    tokens.append(Token(GL_MUL, pos_start=pos_start))
            elif self.current_char == "/":
                pos_start = self.pos.copy()
                self.advance()
                if self.current_char == "/":
                    self.advance()
                    if self.current_char == "=":
                        tokens.append(
                            Token(GL_FLOORDIVEQ, pos_start=pos_start, pos_end=self.pos)
                        )
                        self.advance()
                    else:
                        tokens.append(
                            Token(GL_FLOORDIV, pos_start=pos_start, pos_end=self.pos)
                        )
                elif self.current_char == "=":
                    tokens.append(
                        Token(GL_DIVEQ, pos_start=pos_start, pos_end=self.pos)
                    )
                    self.advance()
                else:
                    tokens.append(Token(GL_DIV, pos_start=pos_start))
            elif self.current_char == "%":
                pos_start = self.pos.copy()
                self.advance()
                if self.current_char == "=":
                    tokens.append(
                        Token(GL_MODEQ, pos_start=pos_start, pos_end=self.pos)
                    )
                    self.advance()
                else:
                    tokens.append(Token(GL_MOD, pos_start=pos_start))
            elif self.current_char == "&":
                pos_start = self.pos.copy()
                self.advance()
                if self.current_char == "=":
                    tokens.append(
                        Token(GL_BIT_ANDEQ, pos_start=pos_start, pos_end=self.pos)
                    )
                    self.advance()
                else:
                    tokens.append(Token(GL_BIT_AND, pos_start=pos_start))
            elif self.current_char == "|":
                pos_start = self.pos.copy()
                self.advance()
                if self.current_char == "=":
                    tokens.append(
                        Token(GL_BIT_OREQ, pos_start=pos_start, pos_end=self.pos)
                    )
                    self.advance()
                else:
                    tokens.append(Token(GL_BIT_OR, pos_start=pos_start))
            elif self.current_char == "~":
                tokens.append(Token(GL_BIT_NOT, pos_start=self.pos))
                self.advance()
            elif self.current_char == "^":
                pos_start = self.pos.copy()
                self.advance()
                if self.current_char == "=":
                    tokens.append(
                        Token(GL_BIT_XOREQ, pos_start=pos_start, pos_end=self.pos)
                    )
                    self.advance()
                else:
                    tokens.append(Token(GL_BIT_XOR, pos_start=pos_start))
            elif self.current_char == "<":
                pos_start = self.pos.copy()
                self.advance()
                if self.current_char == "<":
                    self.advance()
                    if self.current_char == "=":
                        tokens.append(
                            Token(GL_LSHIFTEQ, pos_start=pos_start, pos_end=self.pos)
                        )
                        self.advance()
                    else:
                        tokens.append(
                            Token(GL_LSHIFT, pos_start=pos_start, pos_end=self.pos)
                        )
                elif self.current_char == "=":
                    tokens.append(Token(GL_LTE, pos_start=pos_start, pos_end=self.pos))
                    self.advance()
                else:
                    tokens.append(Token(GL_LT, pos_start=pos_start))
            elif self.current_char == ">":
                pos_start = self.pos.copy()
                self.advance()
                if self.current_char == ">":
                    self.advance()
                    if self.current_char == "=":
                        tokens.append(
                            Token(GL_RSHIFTEQ, pos_start=pos_start, pos_end=self.pos)
                        )
                        self.advance()
                    else:
                        tokens.append(
                            Token(GL_RSHIFT, pos_start=pos_start, pos_end=self.pos)
                        )
                elif self.current_char == "=":
                    tokens.append(Token(GL_GTE, pos_start=pos_start, pos_end=self.pos))
                    self.advance()
                else:
                    tokens.append(Token(GL_GT, pos_start=pos_start))
            elif self.current_char == "(":
                tokens.append(Token(GL_LPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ")":
                tokens.append(Token(GL_RPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ",":
                tokens.append(Token(GL_COMMA, pos_start=self.pos))
                self.advance()
            elif self.current_char == ".":
                tokens.append(Token(GL_DOT, pos_start=self.pos))
                self.advance()
            elif self.current_char == "[":
                tokens.append(Token(GL_LSQUARE, pos_start=self.pos))
                self.advance()
            elif self.current_char == "]":
                tokens.append(Token(GL_RSQUARE, pos_start=self.pos))
                self.advance()
            elif self.current_char == "!":
                tok, error = self.make_not_equals()
                if error:
                    return [], error

                tokens.append(tok)
            elif self.current_char == "=":
                tokens.append(self.make_equals())
            elif self.current_char == "`":
                result = self.make_template_string()
                if isinstance(result, tuple):
                    return [], result[1]

                tokens += result
            elif self.current_char == "{":
                tokens.append(Token(GL_LBRACE, pos_start=self.pos))
                self.advance()
            elif self.current_char == "}":
                tokens.append(Token(GL_RBRACE, pos_start=self.pos))
                self.advance()
            elif self.current_char == ":":
                tokens.append(Token(GL_COLON, pos_start=self.pos))
                self.advance()
            elif self.current_char == "?":
                tokens.append(Token(GL_QMARK, pos_start=self.pos))
                self.advance()
            elif self.current_char == ";":
                tokens.append(Token(GL_SEMI, pos_start=self.pos))
                self.advance()
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()

                return [], IllegalCharError(pos_start, self.pos, "'" + char + "'")

        tokens.append(Token(GL_EOF, pos_start=self.pos))

        return tokens, None
