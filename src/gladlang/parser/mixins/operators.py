"""Binary operator helper and bitwise/shift operators."""

from gladlang.core.constants import (
    GL_BIT_OR,
    GL_BIT_XOR,
    GL_BIT_AND,
    GL_LSHIFT,
    GL_RSHIFT,
)
from gladlang.parser.ast import BinOpNode
from gladlang.parser.parse_result import ParseResult


class ParserOperators:
    def bin_op(self, func_a, ops, func_b=None):
        if func_b is None:
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

    def bitwise_or_expr(self):
        return self.bin_op(self.bitwise_xor_expr, (GL_BIT_OR,))

    def bitwise_xor_expr(self):
        return self.bin_op(self.bitwise_and_expr, (GL_BIT_XOR,))

    def bitwise_and_expr(self):
        return self.bin_op(self.shift_expr, (GL_BIT_AND,))

    def shift_expr(self):
        return self.bin_op(self.arith_expr, (GL_LSHIFT, GL_RSHIFT))
