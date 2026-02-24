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

    scope.set("NULL", Number.null.copy())
    scope.set("FALSE", Number.false.copy())
    scope.set("TRUE", Number.true.copy())

    scope.set("Number", Type("Number"))
    scope.set("String", Type("String"))
    scope.set("List", Type("List"))
    scope.set("Dict", Type("Dict"))
    scope.set("Enum", Type("Enum"))
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
    cleaned = []
    in_str = False
    in_multi = False
    i = 0
    while i < len(text):
        ch = text[i]
        if in_multi:
            cleaned.append(ch)
            if text[i : i + 3] == '"""':
                in_multi = False
                cleaned.append('""')
                i += 3
                continue
        elif in_str:
            cleaned.append(ch)
            if ch == "\\":
                i += 1
            elif ch == '"':
                in_str = False
        elif text[i : i + 3] == '"""':
            in_multi = True
            cleaned.append(ch)
            i += 3
            continue
        elif ch == '"':
            in_str = True
            cleaned.append(ch)
        elif ch == "#":
            while i < len(text) and text[i] != "\n":
                i += 1
            continue
        else:
            cleaned.append(ch)
        i += 1
    text = "".join(cleaned)

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

    pattern = r"(\[|\]|\b(DEF|CLASS|ENUM|IF|ELSE\s+IF|ELSE|WHILE|FOR|TRY|SWITCH|ENDDEF|ENDCLASS|ENDENUM|ENDIF|ENDWHILE|ENDFOR|ENDTRY|ENDSWITCH)\b)"

    tokens = re.finditer(pattern, temp_text)

    start_keys = {"DEF", "CLASS", "ENUM", "IF", "WHILE", "FOR", "TRY", "SWITCH"}

    end_keys = {
        "ENDDEF",
        "ENDCLASS",
        "ENDENUM",
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

    GLADLANG_VERSION = "0.2.0"
    GLADLANG_HELP = f"""
Usage: gladlang [command] [filename/code] [args...]

Commands:
  <no arguments>           Start the interactive GladLang shell.
  [filename.glad]          Execute a GladLang script file.
  ["code string"]          Execute inline GladLang code directly.
  [filename.glad] [args]   Execute script and pass args to INPUT().
  ["code string"] [args]   Execute inline code and pass args to INPUT().
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

                    result, error = run(
                        "<stdin>",
                        full_text,
                        repl_context,
                        instruction_limit=MAX_INSTRUCTIONS,
                    )

                    if error:
                        sys.stdout.write(error.as_string() + "\n")
                    elif result:
                        clean_text = re.sub(r"#.*", "", full_text).strip()

                        if (
                            clean_text.startswith("LET ")
                            or clean_text.startswith("ENUM ")
                            or clean_text.startswith("FINAL ")
                        ):
                            pass
                        elif isinstance(result, Number) and result.value == 0:
                            statement_starters = (
                                "WHILE ",
                                "FOR ",
                                "IF ",
                                "PRINT",
                                "PRINTLN",
                                "SWITCH ",
                                "TRY ",
                                "THROW ",
                            )
                            is_statement = any(
                                clean_text.startswith(s) for s in statement_starters
                            )
                            if not is_statement:
                                sys.stdout.write(str(result) + "\n")
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
                arg_input = arg
                script_args = sys.argv[2:]

                if script_args:
                    sys.stdin = io.StringIO("\n".join(script_args) + "\n")

                is_file = False
                try:
                    is_file = Path(arg_input).is_file()
                except OSError:
                    pass

                if is_file or arg_input.endswith(".glad"):
                    text = Path(arg_input).read_text(encoding="utf-8")
                    source_name = arg_input
                else:
                    text = arg_input
                    source_name = "<cmdline>"

                result, error = run(
                    source_name, text, instruction_limit=MAX_INSTRUCTIONS
                )

                if error:
                    sys.stderr.write(error.as_string() + "\n")

            except MemoryError:
                sys.stderr.write("System Error: Memory Limit Exceeded\n")
            except FileNotFoundError:
                sys.stderr.write(f"File not found: '{arg_input}'\n")
            except Exception as e:
                sys.stderr.write(f"An unexpected error occurred: {e}\n")

    else:
        sys.stdout.write("Error: Invalid arguments.\n")
        sys.stdout.write(GLADLANG_HELP + "\n")


if __name__ == "__main__":
    main()
