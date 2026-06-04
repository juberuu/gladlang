"""List and dictionary literals, comprehensions, and iteration variable parsing."""

from gladlang.core.constants import (
    GL_KEYWORD,
    GL_LSQUARE,
    GL_RSQUARE,
    GL_COMMA,
    GL_LBRACE,
    GL_RBRACE,
    GL_COLON,
    GL_IDENTIFIER,
)
from gladlang.core.errors import InvalidSyntaxError
from gladlang.parser.ast import ListNode, DictNode, ListCompNode, DictCompNode
from gladlang.parser.parse_result import ParseResult


class ParserCollections:
    def parse_iter_vars(self):
        var_toks = []
        res = ParseResult()

        if self.current_tok.type == GL_LSQUARE:
            res.register_advancement()
            self.advance()

            if self.current_tok.type == GL_IDENTIFIER:
                var_toks.append(self.current_tok)
                res.register_advancement()
                self.advance()

                while self.current_tok.type == GL_COMMA:
                    res.register_advancement()
                    self.advance()
                    if self.current_tok.type != GL_IDENTIFIER:
                        return None, res.failure(
                            InvalidSyntaxError(
                                self.current_tok.pos_start,
                                self.current_tok.pos_end,
                                "Expected identifier",
                            )
                        )

                    var_toks.append(self.current_tok)
                    res.register_advancement()
                    self.advance()

            if self.current_tok.type != GL_RSQUARE:
                return None, res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected ']'",
                    )
                )

            res.register_advancement()
            self.advance()

            return var_toks, res

        elif self.current_tok.type == GL_IDENTIFIER:
            var_toks.append(self.current_tok)
            res.register_advancement()
            self.advance()

            return var_toks, res

        return None, None

    def list_expr(self):
        res = ParseResult()
        element_nodes = []
        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.type != GL_LSQUARE:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end, "Expected '['"
                )
            )

        res.register_advancement()
        self.advance()

        if self.current_tok.type == GL_RSQUARE:
            res.register_advancement()
            self.advance()

            return res.success(
                ListNode([], pos_start, self.current_tok.pos_start.copy())
            )

        first_expr = res.register(self.expr())
        if res.error:
            return res

        if self.current_tok.matches(GL_KEYWORD, "FOR"):
            iteration_specs = []

            while self.current_tok.matches(GL_KEYWORD, "FOR"):
                res.register_advancement()
                self.advance()

                var_name_toks, var_res = self.parse_iter_vars()
                if var_res and var_res.error:
                    return res.failure(var_res.error)

                if not var_name_toks:
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_tok.pos_start,
                            self.current_tok.pos_end,
                            "Expected identifier or '[...]'",
                        )
                    )

                res.advance_count += var_res.advance_count

                if not self.current_tok.matches(GL_KEYWORD, "IN"):
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_tok.pos_start,
                            self.current_tok.pos_end,
                            "Expected 'IN'",
                        )
                    )

                res.register_advancement()
                self.advance()

                iterable = res.register(self.expr())
                if res.error:
                    return res

                condition_node = None
                if self.current_tok.matches(GL_KEYWORD, "IF"):
                    res.register_advancement()
                    self.advance()
                    condition_node = res.register(self.expr())
                    if res.error:
                        return res

                iteration_specs.append((var_name_toks, iterable, condition_node))

            if self.current_tok.type != GL_RSQUARE:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected ']'",
                    )
                )

            res.register_advancement()
            self.advance()

            return res.success(
                ListCompNode(
                    first_expr,
                    iteration_specs,
                    pos_start,
                    self.current_tok.pos_start.copy(),
                )
            )

        element_nodes.append(first_expr)

        while self.current_tok.type == GL_COMMA:
            res.register_advancement()
            self.advance()
            element_nodes.append(res.register(self.expr()))
            if res.error:
                return res

        if self.current_tok.type != GL_RSQUARE:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected ',' or ']'",
                )
            )

        res.register_advancement()
        self.advance()

        return res.success(
            ListNode(element_nodes, pos_start, self.current_tok.pos_start.copy())
        )

    def dict_expr(self):
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.type != GL_LBRACE:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end, "Expected '{'"
                )
            )

        res.register_advancement()
        self.advance()

        if self.current_tok.type == GL_RBRACE:
            res.register_advancement()
            self.advance()
            return res.success(
                DictNode([], pos_start, self.current_tok.pos_start.copy())
            )

        key = res.register(self.expr())
        if res.error:
            return res

        if self.current_tok.type != GL_COLON:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end, "Expected ':'"
                )
            )

        res.register_advancement()
        self.advance()

        value = res.register(self.expr())
        if res.error:
            return res

        if self.current_tok.matches(GL_KEYWORD, "FOR"):
            iteration_specs = []

            while self.current_tok.matches(GL_KEYWORD, "FOR"):
                res.register_advancement()
                self.advance()

                var_name_toks, var_res = self.parse_iter_vars()
                if var_res and var_res.error:
                    return res.failure(var_res.error)

                if not var_name_toks:
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_tok.pos_start,
                            self.current_tok.pos_end,
                            "Expected identifier or '[...]'",
                        )
                    )

                res.advance_count += var_res.advance_count

                if not self.current_tok.matches(GL_KEYWORD, "IN"):
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_tok.pos_start,
                            self.current_tok.pos_end,
                            "Expected 'IN'",
                        )
                    )

                res.register_advancement()
                self.advance()

                iterable = res.register(self.expr())
                if res.error:
                    return res

                condition_node = None
                if self.current_tok.matches(GL_KEYWORD, "IF"):
                    res.register_advancement()
                    self.advance()
                    condition_node = res.register(self.expr())
                    if res.error:
                        return res

                iteration_specs.append((var_name_toks, iterable, condition_node))

            if self.current_tok.type != GL_RBRACE:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected '}'",
                    )
                )

            res.register_advancement()
            self.advance()

            return res.success(
                DictCompNode(
                    key,
                    value,
                    iteration_specs,
                    pos_start,
                    self.current_tok.pos_start.copy(),
                )
            )

        kv_pairs = [(key, value)]

        while self.current_tok.type == GL_COMMA:
            res.register_advancement()
            self.advance()

            if self.current_tok.type == GL_RBRACE:
                break

            key = res.register(self.expr())
            if res.error:
                return res

            if self.current_tok.type != GL_COLON:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected ':'",
                    )
                )

            res.register_advancement()
            self.advance()

            value = res.register(self.expr())
            if res.error:
                return res

            kv_pairs.append((key, value))

        if self.current_tok.type != GL_RBRACE:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end, "Expected '}'"
                )
            )

        res.register_advancement()
        self.advance()

        return res.success(
            DictNode(kv_pairs, pos_start, self.current_tok.pos_start.copy())
        )
