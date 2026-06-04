"""Class definitions and instantiation."""

from gladlang.core.constants import (
    GL_KEYWORD,
    GL_IDENTIFIER,
    GL_COMMA,
    GL_LPAREN,
    GL_RPAREN,
    GL_EOF,
)
from gladlang.core.errors import InvalidSyntaxError
from gladlang.lexer.token import Token
from gladlang.parser.ast import (
    ClassNode,
    NewInstanceNode,
    VarAccessNode,
    VarAssignNode,
    FinalVarAssignNode,
    VisibilityStmtNode,
)
from gladlang.parser.parse_result import ParseResult


class ParserClasses:
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

            while self.current_tok.type == GL_KEYWORD and self.current_tok.value in (
                "PUBLIC",
                "PRIVATE",
                "PROTECTED",
                "STATIC",
            ):
                if self.current_tok.value == "STATIC":
                    is_static = True
                else:
                    visibility = self.current_tok.value
                res.register_advancement()
                self.advance()

            if self.current_tok.matches(GL_KEYWORD, "DEF"):
                method_node = res.register(self.fun_def())
                if res.error:
                    return res

                if method_node.var_name_tok is None:
                    return res.failure(
                        InvalidSyntaxError(
                            method_node.pos_start,
                            method_node.pos_end,
                            "Anonymous functions are not allowed inside a class body, methods must have a name",
                        )
                    )

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
                is_final_decl = self.current_tok.matches(GL_KEYWORD, "FINAL")
                if is_final_decl and not is_static:
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_tok.pos_start,
                            self.current_tok.pos_end,
                            "Class-level constants must be declared with STATIC FINAL",
                        )
                    )

                assign_node = res.register(self.statement())
                if res.error:
                    return res

                if not isinstance(
                    assign_node, (VarAssignNode, FinalVarAssignNode, VisibilityStmtNode)
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
