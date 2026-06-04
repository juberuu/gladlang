"""Core parser state, token management, nesting depth, and top‑level parse."""

from gladlang.core.constants import (
    GL_EOF,
    GL_KEYWORD,
    GL_LPAREN,
    GL_RPAREN,
    GL_LBRACE,
    GL_RBRACE,
    GL_LSQUARE,
    GL_RSQUARE,
)
from gladlang.core.errors import InvalidSyntaxError
from gladlang.parser.ast import StatementListNode
from gladlang.parser.parse_result import ParseResult


class ParserBase:
    MAX_NESTING = 200

    def __init__(self, tokens):
        self.tokens = tokens
        self.tok_idx = -1
        self.loop_count = 0
        self.advance()

    def advance(self):
        self.tok_idx += 1
        if self.tok_idx < len(self.tokens):
            self.current_tok = self.tokens[self.tok_idx]

        return self.current_tok

    def check_nesting_depth(self):
        paren_depth = brace_depth = bracket_depth = 0
        max_paren = max_brace = max_bracket = 0

        for tok in self.tokens:
            if tok.type == GL_LPAREN:
                paren_depth += 1
                max_paren = max(max_paren, paren_depth)
            elif tok.type == GL_RPAREN:
                paren_depth = max(0, paren_depth - 1)
            elif tok.type == GL_LBRACE:
                brace_depth += 1
                max_brace = max(max_brace, brace_depth)
            elif tok.type == GL_RBRACE:
                brace_depth = max(0, brace_depth - 1)
            elif tok.type == GL_LSQUARE:
                bracket_depth += 1
                max_bracket = max(max_bracket, bracket_depth)
            elif tok.type == GL_RSQUARE:
                bracket_depth = max(0, bracket_depth - 1)

        worst = max(max_paren, max_brace, max_bracket)
        if worst > self.MAX_NESTING:
            first = self.tokens[0] if self.tokens else None

            last = self.tokens[-1] if self.tokens else None

            return ParseResult().failure(
                InvalidSyntaxError(
                    first.pos_start if first else None,
                    last.pos_end if last else None,
                    f"Expression nesting depth ({worst}) exceeds limit ({self.MAX_NESTING})",
                )
            )
        return None

    def parse(self):
        depth_error = self.check_nesting_depth()
        if depth_error:
            return depth_error

        res = ParseResult()
        statements = []
        pos_start = self.current_tok.pos_start.copy()

        while self.current_tok.type != GL_EOF:
            if self.current_tok.type == GL_KEYWORD and self.current_tok.value in (
                "ENDDEF",
                "ENDIF",
                "ENDCLASS",
                "ENDWHILE",
                "ENDFOR",
                "ENDENUM",
            ):
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        f"Unexpected '{self.current_tok.value}'",
                    )
                )
            statement = res.register(self.statement())
            if res.error:
                return res
            statements.append(statement)

        return res.success(
            StatementListNode(statements, pos_start, self.current_tok.pos_start.copy())
        )

    def statement_list(self, end_keywords):
        res = ParseResult()
        statements = []
        pos_start = self.current_tok.pos_start.copy()

        while self.current_tok.type != GL_EOF and not (
            self.current_tok.type == GL_KEYWORD
            and self.current_tok.value in end_keywords
        ):
            statements.append(res.register(self.statement()))
            if res.error:
                return res

        return res.success(
            StatementListNode(statements, pos_start, self.current_tok.pos_start.copy())
        )
