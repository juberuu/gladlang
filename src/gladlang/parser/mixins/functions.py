"""Function definitions (named and anonymous)."""

from gladlang.core.constants import (
    GL_KEYWORD,
    GL_IDENTIFIER,
    GL_LPAREN,
    GL_RPAREN,
    GL_COMMA,
)
from gladlang.core.errors import InvalidSyntaxError
from gladlang.parser.ast import FunDefNode
from gladlang.parser.parse_result import ParseResult


class ParserFunctions:
    def fun_def(self):
        res = ParseResult()

        if not self.current_tok.matches(GL_KEYWORD, "DEF"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected 'DEF'",
                )
            )

        res.register_advancement()
        self.advance()

        if self.current_tok.type == GL_IDENTIFIER:
            var_name_tok = self.current_tok
            res.register_advancement()
            self.advance()
            if self.current_tok.type != GL_LPAREN:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected '(' after function name",
                    )
                )
        else:
            var_name_tok = None
            if self.current_tok.type != GL_LPAREN:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected '('",
                    )
                )

        res.register_advancement()
        self.advance()
        arg_name_toks = []

        if self.current_tok.type != GL_RPAREN:
            if self.current_tok.type == GL_IDENTIFIER:
                arg_name_toks.append(self.current_tok)
            elif self.current_tok.matches(GL_KEYWORD, "THIS"):
                arg_name_toks.append(self.current_tok)
            else:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected identifier",
                    )
                )

            res.register_advancement()
            self.advance()

            while self.current_tok.type == GL_COMMA:
                res.register_advancement()
                self.advance()

                if self.current_tok.type == GL_IDENTIFIER:
                    arg_name_toks.append(self.current_tok)
                elif self.current_tok.matches(GL_KEYWORD, "THIS"):
                    arg_name_toks.append(self.current_tok)
                else:
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_tok.pos_start,
                            self.current_tok.pos_end,
                            "Expected identifier",
                        )
                    )

                res.register_advancement()
                self.advance()

        if self.current_tok.type != GL_RPAREN:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected ',' or ')'",
                )
            )

        res.register_advancement()
        self.advance()

        saved_loop_count = self.loop_count
        self.loop_count = 0
        body = res.register(self.statement_list(("ENDDEF",)))
        self.loop_count = saved_loop_count

        if res.error:
            return res

        if not self.current_tok.matches(GL_KEYWORD, "ENDDEF"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected 'ENDDEF'",
                )
            )

        res.register_advancement()
        self.advance()

        return res.success(FunDefNode(var_name_tok, arg_name_toks, body))
