"""Enum definitions."""

from gladlang.core.constants import (
    GL_KEYWORD,
    GL_IDENTIFIER,
    GL_EQ,
    GL_COMMA,
    GL_EOF,
)
from gladlang.core.errors import InvalidSyntaxError
from gladlang.parser.ast import EnumNode
from gladlang.parser.parse_result import ParseResult


class ParserEnums:
    def enum_def(self):
        res = ParseResult()

        if not self.current_tok.matches(GL_KEYWORD, "ENUM"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected 'ENUM'",
                )
            )

        res.register_advancement()
        self.advance()

        if self.current_tok.type != GL_IDENTIFIER:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected enum name",
                )
            )

        enum_name_tok = self.current_tok
        pos_start = enum_name_tok.pos_start.copy()
        res.register_advancement()
        self.advance()

        cases = []
        while self.current_tok.type != GL_EOF and not self.current_tok.matches(
            GL_KEYWORD, "ENDENUM"
        ):
            if self.current_tok.type != GL_IDENTIFIER:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected identifier or 'ENDENUM'",
                    )
                )

            case_name_tok = self.current_tok
            res.register_advancement()
            self.advance()

            case_val_node = None
            if self.current_tok.type == GL_EQ:
                res.register_advancement()
                self.advance()
                case_val_node = res.register(self.expr())
                if res.error:
                    return res

            cases.append((case_name_tok, case_val_node))

            if self.current_tok.type == GL_COMMA:
                res.register_advancement()
                self.advance()

        if not self.current_tok.matches(GL_KEYWORD, "ENDENUM"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected 'ENDENUM'",
                )
            )

        pos_end = self.current_tok.pos_end.copy()
        res.register_advancement()
        self.advance()

        return res.success(EnumNode(enum_name_tok, cases, pos_start, pos_end))
