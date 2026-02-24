from .constants import *
import codecs
from functools import lru_cache
from .errors import Position, IllegalCharError, InvalidSyntaxError


@lru_cache(maxsize=1024)
def decode_escapes(s):
    try:
        return codecs.decode(s, "unicode_escape")
    except Exception:
        return s


class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value

        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance()

        if pos_end:
            self.pos_end = pos_end.copy()

    def matches(self, type_, value):
        return self.type == type_ and self.value == value

    def __repr__(self):
        if self.value is not None:
            return f"{self.type}:{self.value}"
        return f"{self.type}"


class Lexer:
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

        while self.current_char != "\n" and self.current_char != None:
            self.advance()

    def make_tokens(self):
        tokens = []

        while self.current_char != None:
            if self.current_char in " \t\r\n":
                self.advance()
            elif self.current_char == "#":
                self.skip_comment()
            elif self.current_char in DIGITS:
                tok_or_tuple = self.make_number()
                if isinstance(tok_or_tuple, tuple):
                    return [], tok_or_tuple[1]
                tokens.append(tok_or_tuple)
            elif self.current_char.isidentifier():
                tokens.append(self.make_identifier())
            elif self.current_char == '"':
                tok_or_tuple = self.make_string()
                if isinstance(tok_or_tuple, tuple):
                    return [], tok_or_tuple[1]
                tokens.append(tok_or_tuple)
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

        while self.current_char != None and self.current_char in DIGITS + ".":
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

    def make_identifier(self):
        id_str = ""
        pos_start = self.pos.copy()

        while self.current_char != None and (id_str + self.current_char).isidentifier():
            id_str += self.current_char
            self.advance()

        tok_type = GL_KEYWORD if id_str in KEYWORDS else GL_IDENTIFIER
        return Token(tok_type, id_str, pos_start, self.pos)

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

    def make_template_string(self):
        tokens = []
        pos_start = self.pos.copy()
        self.advance()

        tokens.append(Token(GL_LPAREN, pos_start=pos_start))

        string_part = ""
        escape_character = False

        while self.current_char != None and (
            self.current_char != "`" or escape_character
        ):

            if not escape_character and self.current_char == "$" and self.peek() == "{":
                tokens.append(Token(GL_STRING, string_part, pos_start=pos_start))
                string_part = ""

                tokens.append(Token(GL_PLUS, pos_start=self.pos))
                tokens.append(Token(GL_IDENTIFIER, "STR", pos_start=self.pos))
                tokens.append(Token(GL_LPAREN, pos_start=self.pos))

                self.advance()
                self.advance()

                expr_str = ""
                brace_count = 1
                while self.current_char != None and brace_count > 0:
                    if self.current_char == "{":
                        brace_count += 1
                    elif self.current_char == "}":
                        brace_count -= 1

                    if brace_count > 0:
                        expr_str += self.current_char
                        self.advance()

                sub_lexer = Lexer(self.fn, expr_str)
                sub_tokens, error = sub_lexer.make_tokens()

                if error:
                    return [], error

                if sub_tokens and sub_tokens[-1].type == GL_EOF:
                    sub_tokens.pop()

                tokens.extend(sub_tokens)

                tokens.append(Token(GL_RPAREN, pos_start=self.pos))
                tokens.append(Token(GL_PLUS, pos_start=self.pos))

                self.advance()

            elif escape_character:
                if self.current_char == "n":
                    string_part += "\n"
                elif self.current_char == "t":
                    string_part += "\t"
                elif self.current_char == "r":
                    string_part += "\r"
                elif self.current_char == "`":
                    string_part += "`"
                elif self.current_char == "\\":
                    string_part += "\\"
                elif self.current_char == '"':
                    string_part += '"'
                elif self.current_char == "'":
                    string_part += "'"
                elif self.current_char == "$":
                    string_part += "$"
                else:
                    string_part += self.current_char

                escape_character = False
                self.advance()

            elif self.current_char == "\\":
                escape_character = True
                self.advance()

            else:
                string_part += self.current_char
                self.advance()

        tokens.append(Token(GL_STRING, string_part, pos_start=pos_start))
        tokens.append(Token(GL_RPAREN, pos_start=self.pos))

        self.advance()
        return tokens

    def make_string(self):
        string = ""
        pos_start = self.pos.copy()

        is_multiline = False

        self.advance()

        if self.current_char == '"' and self.peek() == '"':
            is_multiline = True
            self.advance()
            self.advance()

        escape_character = False

        while self.current_char != None:
            if escape_character:
                if self.current_char == "n":
                    string += "\n"
                elif self.current_char == "t":
                    string += "\t"
                elif self.current_char == '"':
                    string += '"'
                elif self.current_char == "\\":
                    string += "\\"
                else:
                    string += self.current_char
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
                            string += '""'
                    else:
                        string += '"'
                else:
                    break
            else:
                string += self.current_char

            self.advance()

        if self.current_char is None:
            return None, InvalidSyntaxError(
                pos_start, self.pos, "Unterminated string literal"
            )

        self.advance()
        return Token(GL_STRING, string, pos_start, self.pos)
