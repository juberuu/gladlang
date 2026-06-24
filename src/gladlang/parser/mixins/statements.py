"""Top‑level statement parsing (IF, WHILE, FOR, LET, RETURN, PRINT, visibility, BREAK, CONTINUE, etc.)."""

from gladlang.core.constants import (
    GL_KEYWORD,
    GL_IDENTIFIER,
    GL_LSQUARE,
    GL_RSQUARE,
    GL_EQ,
    GL_INT,
    GL_EOF,
    GL_COMMA,
    GL_SEMI,
    GL_LPAREN,
    GL_RPAREN,
)
from gladlang.core.errors import InvalidSyntaxError
from gladlang.parser.ast import (
    IfNode,
    WhileNode,
    ForNode,
    CForNode,
    BreakNode,
    ContinueNode,
    VarAssignNode,
    MultiVarAssignNode,
    ListSetNode,
    VarAccessNode,
    ReturnNode,
    PrintNode,
    NumberNode,
    SetAttrNode,
    VisibilityStmtNode,
    ThrowNode,
)
from gladlang.lexer.token import Token
from gladlang.parser.parse_result import ParseResult


class ParserStatements:
    def statement(self):
        res = ParseResult()

        if self.current_tok.type == GL_KEYWORD and self.current_tok.value in (
            "PUBLIC",
            "PRIVATE",
            "PROTECTED",
            "FINAL",
        ):
            visibility = "PUBLIC"
            is_final = False
            while self.current_tok.type == GL_KEYWORD and self.current_tok.value in (
                "PUBLIC",
                "PRIVATE",
                "PROTECTED",
                "FINAL",
            ):
                if self.current_tok.value == "FINAL":
                    is_final = True
                else:
                    visibility = self.current_tok.value
                res.register_advancement()
                self.advance()

            if self.current_tok.matches(GL_KEYWORD, "ENUM"):
                enum_node = res.register(self.enum_def())
                if res.error:
                    return res

                enum_node.visibility = visibility

                return res.success(enum_node)

            expr = res.register(self.expr())
            if res.error:
                return res

            if isinstance(expr, (SetAttrNode, VarAssignNode)):
                return res.success(
                    VisibilityStmtNode(visibility, expr, is_final=is_final)
                )

            return res.failure(
                InvalidSyntaxError(
                    expr.pos_start,
                    expr.pos_end,
                    "Visibility modifiers can only be used with variable or attribute assignments",
                )
            )

        if self.current_tok.type == GL_KEYWORD and self.current_tok.value in (
            "PRINT",
            "PRINTLN",
        ):
            is_println = self.current_tok.value == "PRINTLN"
            res.register_advancement()
            self.advance()

            exprs = []
            first_expr = res.register(self.expr())
            if res.error:
                return res

            exprs = [first_expr]

            while self.current_tok.type == GL_COMMA:
                res.register_advancement()
                self.advance()
                exprs.append(res.register(self.expr()))
                if res.error:
                    return res

            return res.success(PrintNode(exprs, should_newline=is_println))

        if self.current_tok.matches(GL_KEYWORD, "IF"):
            res.register_advancement()
            self.advance()

            cases = []
            else_case = None

            condition = res.register(self.expr())
            if res.error:
                return res

            if not self.current_tok.matches(GL_KEYWORD, "THEN"):
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected 'THEN'",
                    )
                )

            res.register_advancement()
            self.advance()

            body = res.register(self.statement_list(("ELSE", "ENDIF")))
            if res.error:
                return res

            cases.append((condition, body))

            while self.current_tok.matches(GL_KEYWORD, "ELSE"):
                next_idx = self.tok_idx + 1
                next_tok_is_if = (
                    next_idx < len(self.tokens)
                    and self.tokens[next_idx].matches(GL_KEYWORD, "IF")
                    and self.tokens[next_idx].pos_start.ln
                    == self.current_tok.pos_start.ln
                )

                if next_tok_is_if:
                    res.register_advancement()
                    self.advance()
                    res.register_advancement()
                    self.advance()
                    condition = res.register(self.expr())
                    if res.error:
                        return res

                    if not self.current_tok.matches(GL_KEYWORD, "THEN"):
                        return res.failure(
                            InvalidSyntaxError(
                                self.current_tok.pos_start,
                                self.current_tok.pos_end,
                                "Expected 'THEN' after ELSE IF",
                            )
                        )

                    res.register_advancement()
                    self.advance()
                    body = res.register(self.statement_list(("ELSE", "ENDIF")))
                    if res.error:
                        return res

                    cases.append((condition, body))
                else:
                    res.register_advancement()
                    self.advance()
                    else_case = res.register(self.statement_list(("ENDIF",)))
                    if res.error:
                        return res

                    break

            if not self.current_tok.matches(GL_KEYWORD, "ENDIF"):
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected 'ENDIF'",
                    )
                )

            res.register_advancement()
            self.advance()
            return res.success(IfNode(cases, else_case))

        if self.current_tok.matches(GL_KEYWORD, "WHILE"):
            return self.while_expr()

        if self.current_tok.matches(GL_KEYWORD, "FOR"):
            return self.for_expr()

        if self.current_tok.matches(GL_KEYWORD, "BREAK"):
            if self.loop_count == 0:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "'BREAK' outside of loop",
                    )
                )
            pos_start = self.current_tok.pos_start.copy()
            res.register_advancement()
            self.advance()

            return res.success(BreakNode(pos_start, self.current_tok.pos_start.copy()))

        if self.current_tok.matches(GL_KEYWORD, "CONTINUE"):
            if self.loop_count == 0:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "'CONTINUE' outside of loop",
                    )
                )

            pos_start = self.current_tok.pos_start.copy()
            res.register_advancement()
            self.advance()
            return res.success(
                ContinueNode(pos_start, self.current_tok.pos_start.copy())
            )

        if self.current_tok.matches(GL_KEYWORD, "LET"):
            res.register_advancement()
            self.advance()

            if self.current_tok.type == GL_LSQUARE:
                res.register_advancement()
                self.advance()
                var_names = []
                if self.current_tok.type == GL_IDENTIFIER:
                    var_names.append(self.current_tok)
                    res.register_advancement()
                    self.advance()
                    while self.current_tok.type == GL_COMMA:
                        res.register_advancement()
                        self.advance()
                        if self.current_tok.type == GL_IDENTIFIER:
                            var_names.append(self.current_tok)
                            res.register_advancement()
                            self.advance()
                        else:
                            return res.failure(
                                InvalidSyntaxError(
                                    self.current_tok.pos_start,
                                    self.current_tok.pos_end,
                                    "Expected identifier",
                                )
                            )

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
                if self.current_tok.type != GL_EQ:
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_tok.pos_start,
                            self.current_tok.pos_end,
                            "Expected '='",
                        )
                    )

                res.register_advancement()
                self.advance()
                expr = res.register(self.expr())
                if res.error:
                    return res

                return res.success(MultiVarAssignNode(var_names, expr))

            elif self.current_tok.type == GL_IDENTIFIER:
                var_name = self.current_tok
                res.register_advancement()
                self.advance()

                if self.current_tok.type == GL_LSQUARE:
                    res.register_advancement()
                    self.advance()
                    index_expr = res.register(self.expr())
                    if res.error:
                        return res

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
                    if self.current_tok.type != GL_EQ:
                        return res.failure(
                            InvalidSyntaxError(
                                self.current_tok.pos_start,
                                self.current_tok.pos_end,
                                "Expected '='",
                            )
                        )

                    res.register_advancement()
                    self.advance()
                    value_expr = res.register(self.expr())
                    if res.error:
                        return res

                    return res.success(
                        ListSetNode(VarAccessNode(var_name), index_expr, value_expr)
                    )

                elif self.current_tok.type == GL_EQ:
                    res.register_advancement()
                    self.advance()
                    expr = res.register(self.expr())
                    if res.error:
                        return res

                    return res.success(
                        VarAssignNode(var_name, expr, is_declaration=True)
                    )
                else:
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_tok.pos_start,
                            self.current_tok.pos_end,
                            "Expected '=' or '['",
                        )
                    )
            else:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected identifier or '['",
                    )
                )

        if self.current_tok.matches(GL_KEYWORD, "RETURN"):
            res.register_advancement()
            self.advance()
            pos_start = self.current_tok.pos_start.copy()
            END_KEYWORDS = {
                "ENDDEF",
                "ELSE",
                "ENDIF",
                "ENDWHILE",
                "ENDFOR",
                "ENDTRY",
                "ENDSWITCH",
                "ENDCLASS",
                "CATCH",
                "FINALLY",
                "CASE",
                "DEFAULT",
            }

            if self.current_tok.type == GL_EOF or (
                self.current_tok.type == GL_KEYWORD
                and self.current_tok.value in END_KEYWORDS
            ):
                null_tok = Token(GL_INT, 0, pos_start, pos_start)
                null_node = NumberNode(null_tok)
                return res.success(ReturnNode(null_node, pos_start, pos_start))

            expr = res.register(self.expr())
            if res.error:
                return res

            return res.success(ReturnNode(expr, pos_start, expr.pos_end))

        if self.current_tok.matches(GL_KEYWORD, "DEF"):
            return self.fun_def()

        if self.current_tok.matches(GL_KEYWORD, "CLASS"):
            return self.class_def()

        if self.current_tok.matches(GL_KEYWORD, "ENUM"):
            return self.enum_def()

        if self.current_tok.matches(GL_KEYWORD, "TRY"):
            return self.try_expr()

        if self.current_tok.matches(GL_KEYWORD, "THROW"):
            throw_pos_start = self.current_tok.pos_start.copy()
            res.register_advancement()
            self.advance()

            expr = res.register(self.expr())
            if res.error:
                return res

            return res.success(ThrowNode(expr, throw_pos_start, expr.pos_end))

        if self.current_tok.matches(GL_KEYWORD, "SWITCH"):
            res.register_advancement()
            self.advance()

            return self.switch_expr()

        expr = res.register(self.expr())
        if res.error:
            return res

        return res.success(expr)

    def while_expr(self):
        res = ParseResult()
        if not self.current_tok.matches(GL_KEYWORD, "WHILE"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected 'WHILE'",
                )
            )

        res.register_advancement()
        self.advance()
        condition = res.register(self.expr())
        if res.error:
            return res

        self.loop_count += 1
        body = res.register(self.statement_list(("ENDWHILE",)))
        self.loop_count -= 1
        if res.error:
            return res

        if not self.current_tok.matches(GL_KEYWORD, "ENDWHILE"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected 'ENDWHILE'",
                )
            )

        res.register_advancement()
        self.advance()

        return res.success(WhileNode(condition, body))

    def for_expr(self):
        res = ParseResult()
        if not self.current_tok.matches(GL_KEYWORD, "FOR"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected 'FOR'",
                )
            )

        pos_start = self.current_tok.pos_start.copy()
        res.register_advancement()
        self.advance()

        if self.current_tok.type == GL_LPAREN:
            res.register_advancement()
            self.advance()
            init_node = None
            if self.current_tok.type != GL_SEMI:
                init_node = res.register(self.statement())
                if res.error:
                    return res

            if self.current_tok.type != GL_SEMI:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected ';'",
                    )
                )

            res.register_advancement()
            self.advance()
            condition_node = None
            if self.current_tok.type != GL_SEMI:
                condition_node = res.register(self.expr())
                if res.error:
                    return res

            if self.current_tok.type != GL_SEMI:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected ';'",
                    )
                )

            res.register_advancement()
            self.advance()
            step_node = None
            if self.current_tok.type != GL_RPAREN:
                step_node = res.register(self.expr())
                if res.error:
                    return res

            if self.current_tok.type != GL_RPAREN:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected ')'",
                    )
                )

            res.register_advancement()
            self.advance()
            self.loop_count += 1
            body_node = res.register(self.statement_list(("ENDFOR",)))
            self.loop_count -= 1
            if res.error:
                return res

            if not self.current_tok.matches(GL_KEYWORD, "ENDFOR"):
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected 'ENDFOR'",
                    )
                )

            pos_end = self.current_tok.pos_end.copy()
            res.register_advancement()
            self.advance()

            return res.success(
                CForNode(
                    init_node, condition_node, step_node, body_node, pos_start, pos_end
                )
            )

        var_name_toks, var_res = self.parse_iter_vars()
        if var_res and var_res.error:
            return res.failure(var_res.error)

        if not var_name_toks:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected identifier or '[...]' for loop variable",
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
        iterable_node = res.register(self.expr())
        if res.error:
            return res

        self.loop_count += 1
        body_node = res.register(self.statement_list(("ENDFOR",)))
        self.loop_count -= 1
        if res.error:
            return res

        if not self.current_tok.matches(GL_KEYWORD, "ENDFOR"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected 'ENDFOR'",
                )
            )

        res.register_advancement()
        self.advance()

        return res.success(ForNode(var_name_toks, iterable_node, body_node))
