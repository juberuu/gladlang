import sys
import re
import io
from pathlib import Path

try:
    import resource
except ImportError:
    resource = None

if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(50000)

if hasattr(sys, "setrecursionlimit"):
    sys.setrecursionlimit(2000)

from .runtime import SymbolTable, Context
from .values import Number, BuiltInFunction, List, Type
from .lexer import Lexer
from .parser import Parser
from .interpreter import Interpreter


def get_fresh_global_scope():
    scope = SymbolTable()

    scope.set("NULL", Number(0))
    scope.set("FALSE", Number(0))
    scope.set("TRUE", Number(1))

    scope.set("Number", Type("Number"))
    scope.set("String", Type("String"))
    scope.set("List", Type("List"))
    scope.set("Dict", Type("Dict"))
    scope.set("Function", Type("Function"))
    scope.set("Object", Type("Object"))

    scope.set("INPUT", BuiltInFunction("INPUT"))
    scope.set("STR", BuiltInFunction("STR"))
    scope.set("INT", BuiltInFunction("INT"))
    scope.set("FLOAT", BuiltInFunction("FLOAT"))
    scope.set("BOOL", BuiltInFunction("BOOL"))

    scope.set("LEN", BuiltInFunction("LEN"))
    scope.set("LENGTH", BuiltInFunction("LEN"))

    return scope


def set_memory_limit(max_mb):
    if resource:
        try:
            soft, hard = resource.getrlimit(resource.RLIMIT_AS)
            limit_bytes = max_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, hard))
        except Exception as e:
            sys.stderr.write(f"Warning: Could not set memory limit: {e}\n")


def run(fn, text, context=None, instruction_limit=None):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()
    if error:
        return None, error

    parser = Parser(tokens)
    ast = parser.parse()
    if ast.error:
        return None, ast.error

    interpreter = Interpreter(instruction_limit=instruction_limit)

    if context is None:
        context = Context("<program>")
        context.symbol_table = get_fresh_global_scope()

    result = interpreter.visit(ast.node, context)

    if result.should_return:
        return result.return_value, result.error

    return result.value, result.error


def is_complete(text):
    text = re.sub(r"#.*", "", text)

    temp_text = re.sub(r'""".*?"""', "", text, flags=re.DOTALL)
    if temp_text.count('"""') % 2 != 0:
        return False

    temp_text = re.sub(r"`[^`]*`", "", temp_text, flags=re.DOTALL)
    if temp_text.count("`") % 2 != 0:
        return False

    temp_text = re.sub(r'"[^"\\]*(\\.[^"\\]*)*"', "", temp_text)
    if temp_text.count('"') % 2 != 0:
        return False

    if temp_text.count("(") != temp_text.count(")"):
        return False
    if temp_text.count("[") != temp_text.count("]"):
        return False
    if temp_text.count("{") != temp_text.count("}"):
        return False

    depth = 0
    bracket_level = 0

    pattern = r"(\[|\]|\b(DEF|CLASS|IF|ELSE\s+IF|ELSE|WHILE|FOR|TRY|SWITCH|ENDDEF|ENDCLASS|ENDIF|ENDWHILE|ENDFOR|ENDTRY|ENDSWITCH)\b)"

    tokens = re.finditer(pattern, temp_text)

    start_keys = {"DEF", "CLASS", "IF", "WHILE", "FOR", "TRY", "SWITCH"}
    end_keys = {
        "ENDDEF",
        "ENDCLASS",
        "ENDIF",
        "ENDWHILE",
        "ENDFOR",
        "ENDTRY",
        "ENDSWITCH",
    }

    for match in tokens:
        token = match.group()

        if token in ("ELSE", "ELSE IF"):
            continue

        if token == "[":
            bracket_level += 1
        elif token == "]":
            bracket_level -= 1
        elif token in start_keys:
            depth += 1
        elif token in end_keys:
            depth -= 1

    return depth <= 0


def main():
    MAX_MEMORY_MB = 512
    MAX_INSTRUCTIONS = 100000

    set_memory_limit(MAX_MEMORY_MB)

    GLADLANG_VERSION = "0.1.8"
    GLADLANG_HELP = f"""
Usage: gladlang [command] [filename] [args...]

Commands:
  <no arguments>           Start the interactive GladLang shell.
  [filename.glad]          Execute a GladLang script file.
  [filename.glad] [args]   Execute script and pass args to INPUT().
  --help                   Show this help message and exit.
  --version                Show the interpreter version and exit.
"""

    if len(sys.argv) == 1:
        sys.stdout.write(f"Welcome to GladLang (v{GLADLANG_VERSION})\n")
        sys.stdout.write("Type 'exit' or 'quit' to close the shell.\n")
        sys.stdout.write("--------------------------------------------------\n")

        repl_context = Context("<repl>")
        repl_context.symbol_table = get_fresh_global_scope()

        full_text = ""

        while True:
            try:
                prompt = "GladLang > " if not full_text else "...        > "

                sys.stdout.write(prompt)
                sys.stdout.flush()

                line = sys.stdin.readline()

                if not line:
                    raise EOFError

                line = line.rstrip("\n")

                if not full_text and line.strip().lower() in ("exit", "quit"):
                    break

                full_text += line + "\n"

                if is_complete(full_text):
                    if full_text.strip() == "":
                        full_text = ""
                        continue

                    result, error = run("<stdin>", full_text, repl_context, instruction_limit=MAX_INSTRUCTIONS)

                    if error:
                        sys.stdout.write(error.as_string() + "\n")
                    elif result:
                        clean_text = re.sub(r"#.*", "", full_text).strip()

                        if clean_text.startswith("LET "):
                            pass
                        elif isinstance(result, Number) and result.value == 0:
                            pass
                        elif (
                            isinstance(result, List)
                            and len(result.elements) == 1
                            and result.elements[0].value == "NULL"
                        ):
                            pass
                        else:
                            sys.stdout.write(str(result) + "\n")

                    full_text = ""

            except KeyboardInterrupt:
                sys.stdout.write("\nKeyboardInterrupt\n")
                full_text = ""
                continue
            except MemoryError:
                sys.stdout.write("System Error: Memory Limit Exceeded\n")
                full_text = ""
            except EOFError:
                sys.stdout.write("\nExiting.\n")
                break
            except Exception as e:
                sys.stdout.write(f"Shell Error: {e}\n")
                full_text = ""

    elif len(sys.argv) >= 2:
        arg = sys.argv[1]

        if arg == "--help":
            sys.stdout.write(GLADLANG_HELP + "\n")

        elif arg == "--version":
            sys.stdout.write(f"GladLang v{GLADLANG_VERSION}\n")

        else:
            try:
                filename = arg

                script_args = sys.argv[2:]

                if script_args:
                    sys.stdin = io.StringIO("\n".join(script_args) + "\n")

                text = Path(filename).read_text(encoding="utf-8")

                result, error = run(filename, text, instruction_limit=MAX_INSTRUCTIONS)

                if error:
                    sys.stderr.write(error.as_string() + "\n")

            except MemoryError:
                sys.stderr.write("System Error: Memory Limit Exceeded\n")
            except FileNotFoundError:
                sys.stderr.write(f"File not found: '{filename}'\n")
            except Exception as e:
                sys.stderr.write(f"An unexpected error occurred: {e}\n")

    else:
        sys.stdout.write("Error: Invalid arguments.\n")
        sys.stdout.write(GLADLANG_HELP + "\n")


if __name__ == "__main__":
    main()
