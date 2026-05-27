"""Interpreter runner – orchestrates lexing, parsing, and execution in one call."""


def run(fn, text, context=None, instruction_limit=None):
    from gladlang.lexer.lexer import Lexer
    from gladlang.parser.parser import Parser
    from gladlang.interpreter.interpreter import Interpreter
    from gladlang.runtime.context import Context
    from gladlang.core.util.source_detach import detach_source_from_node
    from gladlang.core.util.global_scope import get_fresh_global_scope

    lexer = Lexer(fn, text)

    tokens, error = lexer.make_tokens()
    if error:
        return None, error

    parser = Parser(tokens)

    ast = parser.parse()

    if ast.error:
        return None, ast.error

    if ast.node:
        detach_source_from_node(ast.node)

    interpreter = Interpreter(instruction_limit=instruction_limit)

    if context is None:
        context = Context("<program>")
        context.symbol_table = get_fresh_global_scope()

    result = interpreter.visit(ast.node, context)

    if result.should_return:
        return result.return_value, result.error

    return result.value, result.error
