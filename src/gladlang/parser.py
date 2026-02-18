from .constants import *
from .errors import InvalidSyntaxError
from .nodes import *
from .lexer import Token


class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None
        self.advance_count = 0

    def register_advancement(self):
        self.advance_count += 1

    def register(self, res):
        self.advance_count += res.advance_count
        if res.error:
            self.error = res.error
        return res.node

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        if not self.error or self.advance_count == 0:
            self.error = error
        return self


class Parser:
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

    def parse(self):
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
            exprs.append(first_expr)

            while True:
                if self.current_tok.type == GL_COMMA:
                    res.register_advancement()
                    self.advance()
                    exprs.append(res.register(self.expr()))
                    if res.error:
                        return res
                elif self.current_tok.pos_start.ln == exprs[
                    -1
                ].pos_end.ln and self.current_tok.type not in (GL_EOF, GL_KEYWORD):

                    next_expr = res.register(self.expr())
                    if res.error:
                        return res
                    exprs.append(next_expr)
                else:
                    break

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

                is_else_if = False
                if self.tok_idx + 1 < len(self.tokens):
                    if self.tokens[self.tok_idx + 1].matches(GL_KEYWORD, "IF"):
                        is_else_if = True

                if is_else_if:
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
                                "Expected 'THEN'",
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
            res.register_advancement()
            self.advance()

            expr = res.register(self.expr())
            if res.error:
                return res

            return res.success(
                ThrowNode(expr, self.current_tok.pos_start, expr.pos_end)
            )

        if self.current_tok.matches(GL_KEYWORD, "SWITCH"):
            res.register_advancement()
            self.advance()
            return self.switch_expr()

        expr = res.register(self.expr())
        if res.error:
            return res
        return res.success(expr)

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

    def logic_expr(self):
        return self.bin_op(
            self.comp_expr,
            ((GL_KEYWORD, "AND"), (GL_KEYWORD, "OR")),
        )

    def ternary_expr(self):
        res = ParseResult()

        condition_node = res.register(self.logic_expr())
        if res.error:
            return res

        if self.current_tok.type == GL_QMARK:
            res.register_advancement()
            self.advance()

            true_case_node = res.register(self.expr())
            if res.error:
                return res

            if self.current_tok.type != GL_COLON:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected ':' in ternary operator",
                    )
                )

            res.register_advancement()
            self.advance()

            false_case_node = res.register(self.ternary_expr())
            if res.error:
                return res

            return res.success(
                TernaryOpNode(condition_node, true_case_node, false_case_node)
            )

        return res.success(condition_node)

    def expr(self):
        res = ParseResult()

        node = res.register(self.ternary_expr())

        if res.error:
            return res

        if self.current_tok.type in (
            GL_EQ,
            GL_PLUSEQ,
            GL_MINUSEQ,
            GL_MULEQ,
            GL_DIVEQ,
            GL_POWEQ,
            GL_MODEQ,
            GL_FLOORDIVEQ,
            GL_BIT_ANDEQ,
            GL_BIT_OREQ,
            GL_BIT_XOREQ,
            GL_LSHIFTEQ,
            GL_RSHIFTEQ,
        ):
            op_tok = self.current_tok
            res.register_advancement()
            self.advance()

            expr = res.register(self.expr())
            if res.error:
                return res

            if op_tok.type != GL_EQ:
                bin_op_type = None
                if op_tok.type == GL_PLUSEQ:
                    bin_op_type = GL_PLUS
                elif op_tok.type == GL_MINUSEQ:
                    bin_op_type = GL_MINUS
                elif op_tok.type == GL_MULEQ:
                    bin_op_type = GL_MUL
                elif op_tok.type == GL_DIVEQ:
                    bin_op_type = GL_DIV
                elif op_tok.type == GL_POWEQ:
                    bin_op_type = GL_POW
                elif op_tok.type == GL_MODEQ:
                    bin_op_type = GL_MOD
                elif op_tok.type == GL_FLOORDIVEQ:
                    bin_op_type = GL_FLOORDIV
                elif op_tok.type == GL_BIT_ANDEQ:
                    bin_op_type = GL_BIT_AND
                elif op_tok.type == GL_BIT_OREQ:
                    bin_op_type = GL_BIT_OR
                elif op_tok.type == GL_BIT_XOREQ:
                    bin_op_type = GL_BIT_XOR
                elif op_tok.type == GL_LSHIFTEQ:
                    bin_op_type = GL_LSHIFT
                elif op_tok.type == GL_RSHIFTEQ:
                    bin_op_type = GL_RSHIFT

                expr = BinOpNode(
                    node, Token(bin_op_type, pos_start=op_tok.pos_start), expr
                )

            if isinstance(node, VarAccessNode):
                return res.success(
                    VarAssignNode(node.var_name_tok, expr, is_declaration=False)
                )
            elif isinstance(node, GetAttrNode):
                return res.success(
                    SetAttrNode(node.object_node, node.attr_name_tok, expr)
                )
            elif isinstance(node, ListAccessNode):
                return res.success(ListSetNode(node.list_node, node.index_node, expr))
            else:
                return res.failure(
                    InvalidSyntaxError(
                        node.pos_start, node.pos_end, "Invalid assignment target"
                    )
                )

        return res.success(node)

    def comp_expr(self):
        res = ParseResult()

        if self.current_tok.matches(GL_KEYWORD, "NOT"):
            op_tok = self.current_tok
            res.register_advancement()
            self.advance()

            node = res.register(self.comp_expr())
            if res.error:
                return res
            return res.success(UnaryOpNode(op_tok, node))

        node = res.register(self.bitwise_or_expr())
        if res.error:
            return res

        ops = []

        while self.current_tok.type in (GL_EE, GL_NE, GL_LT, GL_GT, GL_LTE, GL_GTE) or (
            self.current_tok.type == GL_KEYWORD
            and self.current_tok.value in ("IS", "INSTANCEOF")
        ):
            op_tok = self.current_tok
            res.register_advancement()
            self.advance()

            right_expr = res.register(self.bitwise_or_expr())
            if res.error:
                return res

            ops.append((op_tok, right_expr))

        if not ops:
            return res.success(node)

        if len(ops) == 1:
            op_tok, right_node = ops[0]
            return res.success(BinOpNode(node, op_tok, right_node))

        return res.success(ChainedCompNode(node, ops))

    def arith_expr(self):
        return self.bin_op(self.term, (GL_PLUS, GL_MINUS))

    def term(self):
        return self.bin_op(self.factor, (GL_MUL, GL_DIV, GL_MOD, GL_FLOORDIV))

    def factor(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (GL_PLUS, GL_MINUS):
            res.register_advancement()
            self.advance()
            factor = res.register(self.factor())
            if res.error:
                return res
            return res.success(UnaryOpNode(tok, factor))

        elif tok.type in (GL_PLUSPLUS, GL_MINUSMINUS):
            op_tok = self.current_tok
            res.register_advancement()
            self.advance()

            node = res.register(self.call())
            if res.error:
                return res

            if not isinstance(node, (VarAccessNode, GetAttrNode, ListAccessNode)):
                return res.failure(
                    InvalidSyntaxError(
                        node.pos_start,
                        op_tok.pos_end,
                        "Invalid target for pre-increment/decrement operator",
                    )
                )

            return res.success(UnaryOpNode(op_tok, node))

        elif tok.type == GL_BIT_NOT:
            res.register_advancement()
            self.advance()
            factor = res.register(self.factor())
            if res.error:
                return res
            return res.success(UnaryOpNode(tok, factor))

        return self.power()

    def power(self):
        return self.bin_op(self.call, (GL_POW,), self.factor)

    def call(self):
        res = ParseResult()
        atom = res.register(self.atom())
        if res.error:
            return res

        while True:
            if self.current_tok.type == GL_LPAREN:
                res.register_advancement()
                self.advance()
                arg_nodes = []

                if self.current_tok.type != GL_RPAREN:
                    arg_nodes.append(res.register(self.expr()))
                    if res.error:
                        return res

                    while self.current_tok.type == GL_COMMA:
                        res.register_advancement()
                        self.advance()

                        arg_nodes.append(res.register(self.expr()))
                        if res.error:
                            return res

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
                atom = CallNode(atom, arg_nodes)

            elif self.current_tok.type == GL_DOT:
                res.register_advancement()
                self.advance()

                if self.current_tok.type != GL_IDENTIFIER:
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_tok.pos_start,
                            self.current_tok.pos_end,
                            "Expected identifier after '.'",
                        )
                    )

                attr_name_tok = self.current_tok
                res.register_advancement()
                self.advance()

                atom = GetAttrNode(atom, attr_name_tok)

            elif self.current_tok.type == GL_LSQUARE:
                res.register_advancement()
                self.advance()

                start_node = res.register(self.expr())
                if res.error:
                    return res

                if self.current_tok.type == GL_COLON:
                    res.register_advancement()
                    self.advance()

                    end_node = None
                    if self.current_tok.type != GL_RSQUARE:
                        end_node = res.register(self.expr())
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
                    atom = SliceAccessNode(atom, start_node, end_node)

                else:
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
                    atom = ListAccessNode(atom, start_node)

            else:
                break

        if self.current_tok.type in (GL_PLUSPLUS, GL_MINUSMINUS):
            if not isinstance(atom, (VarAccessNode, GetAttrNode, ListAccessNode)):
                return res.failure(
                    InvalidSyntaxError(
                        atom.pos_start,
                        self.current_tok.pos_end,
                        "Invalid target for post-increment/decrement operator",
                    )
                )

            op_tok = self.current_tok
            res.register_advancement()
            self.advance()
            atom = PostOpNode(atom, op_tok)

        return res.success(atom)

    def atom(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type == GL_LBRACE:
            return self.dict_expr()

        if tok.type in (GL_INT, GL_FLOAT):
            res.register_advancement()
            self.advance()
            return res.success(NumberNode(tok))

        elif tok.type == GL_STRING:
            res.register_advancement()
            self.advance()
            return res.success(StringNode(tok))

        elif tok.type == GL_IDENTIFIER:
            res.register_advancement()
            self.advance()
            return res.success(VarAccessNode(tok))

        elif tok.matches(GL_KEYWORD, "THIS"):
            res.register_advancement()
            self.advance()
            return res.success(VarAccessNode(tok))

        elif tok.matches(GL_KEYWORD, "SUPER"):
            res.register_advancement()
            self.advance()
            return res.success(VarAccessNode(tok))

        elif tok.type == GL_LPAREN:
            res.register_advancement()
            self.advance()
            expr = res.register(self.expr())
            if res.error:
                return res
            if self.current_tok.type == GL_RPAREN:
                res.register_advancement()
                self.advance()
                return res.success(expr)
            else:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected ')'",
                    )
                )

        elif tok.type == GL_LSQUARE:
            return self.list_expr()

        elif tok.matches(GL_KEYWORD, "DEF"):
            return self.fun_def()

        elif tok.matches(GL_KEYWORD, "CLASS"):
            return self.class_def()

        elif tok.matches(GL_KEYWORD, "NEW"):
            return self.new_instance()

        return res.failure(
            InvalidSyntaxError(
                tok.pos_start,
                tok.pos_end,
                "Expected int, float, string, identifier, '+', '-', '++', '--', '(', '[', 'DEF', 'CLASS', or 'NEW'",
            )
        )

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

        body = res.register(self.statement_list(("ENDDEF",)))

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

    def class_def(self):
        res = ParseResult()

        if not self.current_tok.matches(GL_KEYWORD, "CLASS"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected 'CLASS'",
                )
            )

        res.register_advancement()
        self.advance()

        if self.current_tok.type != GL_IDENTIFIER:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected class name",
                )
            )

        class_name_tok = self.current_tok
        res.register_advancement()
        self.advance()

        superclass_nodes = []
        if self.current_tok.matches(GL_KEYWORD, "INHERITS"):
            res.register_advancement()
            self.advance()

            if self.current_tok.type != GL_IDENTIFIER:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected superclass name",
                    )
                )

            superclass_nodes.append(VarAccessNode(self.current_tok))
            res.register_advancement()
            self.advance()

            while self.current_tok.type == GL_COMMA:
                res.register_advancement()
                self.advance()

                if self.current_tok.type != GL_IDENTIFIER:
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_tok.pos_start,
                            self.current_tok.pos_end,
                            "Expected superclass name",
                        )
                    )

                superclass_nodes.append(VarAccessNode(self.current_tok))
                res.register_advancement()
                self.advance()

        method_nodes = []
        static_field_nodes = []

        while self.current_tok.type != GL_EOF and not self.current_tok.matches(
            GL_KEYWORD, "ENDCLASS"
        ):

            visibility = "PUBLIC"
            is_static = False

            if self.current_tok.type == GL_KEYWORD and self.current_tok.value in (
                "PUBLIC",
                "PRIVATE",
                "PROTECTED",
            ):
                visibility = self.current_tok.value
                res.register_advancement()
                self.advance()

            if self.current_tok.matches(GL_KEYWORD, "STATIC"):
                is_static = True
                res.register_advancement()
                self.advance()

            if self.current_tok.type == GL_KEYWORD and self.current_tok.value in (
                "PUBLIC",
                "PRIVATE",
                "PROTECTED",
            ):
                if visibility == "PUBLIC":
                    visibility = self.current_tok.value
                    res.register_advancement()
                    self.advance()

            if self.current_tok.matches(GL_KEYWORD, "DEF"):
                method_node = res.register(self.fun_def())
                if res.error:
                    return res

                method_node.visibility = visibility
                method_node.is_static = is_static

                is_constructor = method_node.var_name_tok.value == class_name_tok.value

                if not is_static:
                    if (
                        len(method_node.arg_name_toks) == 0
                        or method_node.arg_name_toks[0].value != "THIS"
                    ):
                        method_node.arg_name_toks.insert(
                            0,
                            Token(
                                GL_KEYWORD,
                                "THIS",
                                pos_start=method_node.pos_start,
                                pos_end=method_node.pos_start,
                            ),
                        )

                if is_constructor and is_static:
                    return res.failure(
                        InvalidSyntaxError(
                            method_node.pos_start,
                            method_node.pos_end,
                            f"Constructor '{class_name_tok.value}' cannot be STATIC",
                        )
                    )

                method_nodes.append(method_node)

            elif self.current_tok.matches(
                GL_KEYWORD, "LET"
            ) or self.current_tok.matches(GL_KEYWORD, "FINAL"):
                assign_node = res.register(self.statement())
                if res.error:
                    return res

                if not isinstance(
                    assign_node,
                    (VarAssignNode, FinalVarAssignNode, VisibilityStmtNode),
                ):
                    return res.failure(
                        InvalidSyntaxError(
                            assign_node.pos_start,
                            assign_node.pos_end,
                            "Expected variable declaration inside class",
                        )
                    )

                assign_node.is_static = is_static
                assign_node.target_visibility = visibility

                static_field_nodes.append(assign_node)

            elif self.current_tok.matches(GL_KEYWORD, "ENUM"):
                enum_node = res.register(self.enum_def())
                if res.error:
                    return res

                enum_node.visibility = visibility
                enum_node.is_static = True
                static_field_nodes.append(enum_node)

            else:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected 'DEF', 'LET', 'FINAL' or 'STATIC' inside class body",
                    )
                )

        if not self.current_tok.matches(GL_KEYWORD, "ENDCLASS"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected 'ENDCLASS'",
                )
            )

        res.register_advancement()
        self.advance()

        return res.success(
            ClassNode(
                class_name_tok, superclass_nodes, method_nodes, static_field_nodes
            )
        )

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

    def new_instance(self):
        res = ParseResult()

        if not self.current_tok.matches(GL_KEYWORD, "NEW"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected 'NEW'",
                )
            )

        res.register_advancement()
        self.advance()

        if self.current_tok.type != GL_IDENTIFIER:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected class name",
                )
            )

        class_name_tok = self.current_tok
        res.register_advancement()
        self.advance()

        if self.current_tok.type != GL_LPAREN:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected '(' after class name for 'NEW'",
                )
            )

        res.register_advancement()
        self.advance()
        arg_nodes = []

        if self.current_tok.type != GL_RPAREN:
            arg_nodes.append(res.register(self.expr()))
            if res.error:
                return res

            while self.current_tok.type == GL_COMMA:
                res.register_advancement()
                self.advance()

                arg_nodes.append(res.register(self.expr()))
                if res.error:
                    return res

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

        return res.success(NewInstanceNode(class_name_tok, arg_nodes))

    def bin_op(self, func_a, ops, func_b=None):
        if func_b == None:
            func_b = func_a

        res = ParseResult()
        left = res.register(func_a())
        if res.error:
            return res

        while (
            self.current_tok.type in ops
            or (self.current_tok.type, self.current_tok.value) in ops
        ):
            op_tok = self.current_tok
            res.register_advancement()
            self.advance()
            right = res.register(func_b())
            if res.error:
                return res
            left = BinOpNode(left, op_tok, right)

        return res.success(left)

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

        kv_pairs = []
        kv_pairs.append((key, value))

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

    def try_expr(self):
        res = ParseResult()
        res.register_advancement()
        self.advance()

        try_body = res.register(self.statement_list(("CATCH", "FINALLY", "ENDTRY")))
        if res.error:
            return res

        catch_var = None
        catch_body = None
        finally_body = None

        if self.current_tok.matches(GL_KEYWORD, "CATCH"):
            res.register_advancement()
            self.advance()

            if self.current_tok.type == GL_IDENTIFIER:
                catch_var = self.current_tok
                res.register_advancement()
                self.advance()

            catch_body = res.register(self.statement_list(("FINALLY", "ENDTRY")))
            if res.error:
                return res

        if self.current_tok.matches(GL_KEYWORD, "FINALLY"):
            res.register_advancement()
            self.advance()

            finally_body = res.register(self.statement_list(("ENDTRY",)))
            if res.error:
                return res

        if not self.current_tok.matches(GL_KEYWORD, "ENDTRY"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected 'ENDTRY'",
                )
            )

        res.register_advancement()
        self.advance()

        return res.success(
            TryCatchNode(
                try_body,
                catch_var,
                catch_body,
                finally_body,
                try_body.pos_start,
                self.current_tok.pos_start.copy(),
            )
        )

    def switch_expr(self):
        res = ParseResult()
        switch_value = res.register(self.expr())
        if res.error:
            return res

        cases = []
        default_case = None

        while self.current_tok.matches(GL_KEYWORD, "CASE"):
            res.register_advancement()
            self.advance()

            case_conditions = []

            case_conditions.append(res.register(self.expr()))
            if res.error:
                return res

            while self.current_tok.type == GL_COMMA:
                res.register_advancement()
                self.advance()
                case_conditions.append(res.register(self.expr()))
                if res.error:
                    return res

            if self.current_tok.type == GL_COLON:
                res.register_advancement()
                self.advance()

            body = res.register(self.statement_list(("CASE", "DEFAULT", "ENDSWITCH")))
            if res.error:
                return res

            cases.append((case_conditions, body))

        if self.current_tok.matches(GL_KEYWORD, "DEFAULT"):
            res.register_advancement()
            self.advance()

            if self.current_tok.type == GL_COLON:
                res.register_advancement()
                self.advance()

            default_case = res.register(self.statement_list(("ENDSWITCH",)))
            if res.error:
                return res

        if not self.current_tok.matches(GL_KEYWORD, "ENDSWITCH"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected 'ENDSWITCH'",
                )
            )

        res.register_advancement()
        self.advance()

        return res.success(SwitchNode(switch_value, cases, default_case))

    def bitwise_or_expr(self):
        return self.bin_op(self.bitwise_xor_expr, (GL_BIT_OR,))

    def bitwise_xor_expr(self):
        return self.bin_op(self.bitwise_and_expr, (GL_BIT_XOR,))

    def bitwise_and_expr(self):
        return self.bin_op(self.shift_expr, (GL_BIT_AND,))

    def shift_expr(self):
        return self.bin_op(self.arith_expr, (GL_LSHIFT, GL_RSHIFT))
