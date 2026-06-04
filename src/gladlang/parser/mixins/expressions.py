"""Expression parsing (ternary, comparisons, arithmetic, calls, atoms, etc.)."""

from gladlang.core.constants import (
    GL_KEYWORD,
    GL_QMARK,
    GL_COLON,
    GL_EE,
    GL_NE,
    GL_LT,
    GL_GT,
    GL_LTE,
    GL_GTE,
    GL_PLUS,
    GL_MINUS,
    GL_MUL,
    GL_DIV,
    GL_MOD,
    GL_FLOORDIV,
    GL_POW,
    GL_BIT_AND,
    GL_BIT_OR,
    GL_BIT_XOR,
    GL_BIT_NOT,
    GL_LSHIFT,
    GL_RSHIFT,
    GL_LPAREN,
    GL_RPAREN,
    GL_LBRACE,
    GL_LSQUARE,
    GL_INT,
    GL_FLOAT,
    GL_STRING,
    GL_IDENTIFIER,
    GL_PLUSPLUS,
    GL_MINUSMINUS,
    GL_DOT,
    GL_COMMA,
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
    GL_RSQUARE,
)
from gladlang.core.errors import InvalidSyntaxError
from gladlang.parser.ast import (
    NumberNode,
    StringNode,
    VarAccessNode,
    BinOpNode,
    UnaryOpNode,
    TernaryOpNode,
    ChainedCompNode,
    CallNode,
    GetAttrNode,
    SliceAccessNode,
    ListAccessNode,
    PostOpNode,
    VarAssignNode,
    SetAttrNode,
    ListSetNode,
)
from gladlang.lexer.token import Token
from gladlang.parser.parse_result import ParseResult


class ParserExpressions:
    def or_expr(self):
        return self.bin_op(self.and_expr, ((GL_KEYWORD, "OR"),))

    def and_expr(self):
        return self.bin_op(self.comp_expr, ((GL_KEYWORD, "AND"),))

    def logic_expr(self):
        return self.or_expr()

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
                start_node = None
                if self.current_tok.type not in (GL_COLON, GL_RSQUARE):
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
                    if start_node is None:
                        return res.failure(
                            InvalidSyntaxError(
                                self.current_tok.pos_start,
                                self.current_tok.pos_end,
                                "Expected expression before ']'",
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
