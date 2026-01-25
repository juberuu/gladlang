from .constants import *
import codecs
from functools import lru_cache
from .errors import Position, IllegalCharError, InvalidSyntaxError


@lru_cache(maxsize=1024)
def decode_escapes(s):
    try:
        return codecs.decode(s, "unicode_escape")
    except:
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
        if self.value:
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
                tokens.append(self.make_number())
            elif self.current_char.isidentifier():
                tokens.append(self.make_identifier())
            elif self.current_char == '"':
                tokens.append(self.make_string())

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
                    tokens.append(Token(GL_POW, pos_start=pos_start, pos_end=self.pos))
                    self.advance()
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
                tokens += self.make_template_string()
            elif self.current_char == "<":
                tokens.append(self.make_less_than())
            elif self.current_char == ">":
                tokens.append(self.make_greater_than())
            elif self.current_char == "{":
                tokens.append(Token(GL_LBRACE, pos_start=self.pos))
                self.advance()
            elif self.current_char == "}":
                tokens.append(Token(GL_RBRACE, pos_start=self.pos))
                self.advance()
            elif self.current_char == ":":
                tokens.append(Token(GL_COLON, pos_start=self.pos))
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

    def make_string(self, quote_type):
        string_content = ""
        escape_character = False
        self.advance()

        while self.current_char != None and (
            self.current_char != quote_type or escape_character
        ):
            if escape_character:
                string_content += "\\" + self.current_char
                escape_character = False
            else:
                if self.current_char == "\\":
                    escape_character = True
                else:
                    string_content += self.current_char
            self.advance()

        self.advance()

        string_content = decode_escapes(string_content)

        return Token(GL_STRING, string_content, self.pos_start, self.pos)

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

        self.advance()
        return Token(GL_STRING, string, pos_start, self.pos)

    def make_less_than(self):
        tok_type = GL_LT
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == "=":
            self.advance()
            tok_type = GL_LTE

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_greater_than(self):
        tok_type = GL_GT
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == "=":
            self.advance()
            tok_type = GL_GTE

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_plus_equals(self):
        token_type = GL_PLUS
        self.advance()
        if self.current_char == "=":
            self.advance()
            token_type = GL_PLUSEQ
        return Token(token_type, pos_start=self.pos)

    def make_minus_equals(self):
        token_type = GL_MINUS
        self.advance()
        if self.current_char == "=":
            self.advance()
            token_type = GL_MINUSEQ
        return Token(token_type, pos_start=self.pos)

    def make_mul_equals(self):
        token_type = GL_MUL
        self.advance()
        if self.current_char == "=":
            self.advance()
            token_type = GL_MULEQ
        return Token(token_type, pos_start=self.pos)

    def make_div_equals(self):
        token_type = GL_DIV
        self.advance()
        if self.current_char == "=":
            self.advance()
            token_type = GL_DIVEQ
        return Token(token_type, pos_start=self.pos)

    def make_pow_equals(self):
        token_type = GL_POW
        self.advance()
        if self.current_char == "=":
            self.advance()
            token_type = GL_POWEQ
        return Token(token_type, pos_start=self.pos)

    def make_mod_equals(self):
        token_type = GL_MOD
        self.advance()
        if self.current_char == "=":
            self.advance()
            token_type = GL_MODEQ
        return Token(token_type, pos_start=self.pos)
