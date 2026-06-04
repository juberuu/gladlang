"""Core interpreter dispatch, instruction budget, and caching."""

from gladlang.core.constants import (
    GL_PLUS,
    GL_MINUS,
    GL_MUL,
    GL_DIV,
    GL_MOD,
    GL_FLOORDIV,
    GL_POW,
    GL_EE,
    GL_NE,
    GL_LT,
    GL_GT,
    GL_LTE,
    GL_GTE,
    GL_BIT_AND,
    GL_BIT_OR,
    GL_BIT_XOR,
    GL_LSHIFT,
    GL_RSHIFT,
)
from gladlang.core.errors import RTError
from gladlang.runtime.rt_result import RTResult


class InterpreterBase:
    def __init__(self, instruction_limit=None):
        self.dispatch_cache = {}

        self.instruction_limit = instruction_limit

        self._binop_dispatch = {
            GL_PLUS: lambda l, r: l.added_to(r),
            GL_MINUS: lambda l, r: l.subbed_by(r),
            GL_MUL: lambda l, r: l.multed_by(r),
            GL_DIV: lambda l, r: l.dived_by(r),
            GL_MOD: lambda l, r: l.modded_by(r),
            GL_FLOORDIV: lambda l, r: l.floordived_by(r),
            GL_POW: lambda l, r: l.powed_by(r),
            GL_EE: lambda l, r: l.get_comparison_eq(r),
            GL_NE: lambda l, r: l.get_comparison_ne(r),
            GL_LT: lambda l, r: l.get_comparison_lt(r),
            GL_GT: lambda l, r: l.get_comparison_gt(r),
            GL_LTE: lambda l, r: l.get_comparison_lte(r),
            GL_GTE: lambda l, r: l.get_comparison_gte(r),
            GL_BIT_AND: lambda l, r: l.bitted_and_by(r),
            GL_BIT_OR: lambda l, r: l.bitted_or_by(r),
            GL_BIT_XOR: lambda l, r: l.bitted_xor_by(r),
            GL_LSHIFT: lambda l, r: l.lshifted_by(r),
            GL_RSHIFT: lambda l, r: l.rshifted_by(r),
        }

    def visit(self, node, context):
        if self.instruction_limit is not None:
            self.instruction_limit -= 1
            if self.instruction_limit <= 0:
                return RTResult().failure(
                    RTError(
                        node.pos_start,
                        node.pos_end,
                        "Instruction budget exceeded",
                        context,
                    )
                )

        node_type = type(node)
        method = self.dispatch_cache.get(node_type)

        if method is None:
            method_name = f"visit_{node_type.__name__}"
            method = getattr(self, method_name, self.no_visit_method)
            self.dispatch_cache[node_type] = method

        try:
            result = method(node, context)
        except RecursionError:
            return RTResult().failure(
                RTError(
                    node.pos_start,
                    node.pos_end,
                    "Expression too complex (maximum recursion depth exceeded)",
                    context,
                )
            )

        if isinstance(result, RTResult) and (
            result.should_return
            or result.should_break
            or result.should_continue
            or result.error
        ):
            return result

        return result

    def no_visit_method(self, node, context):
        raise Exception(f"No visit_{type(node).__name__} method defined")
