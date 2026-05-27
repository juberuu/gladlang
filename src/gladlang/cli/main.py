"""GladLang command-line interface and interactive REPL.

Provides script execution, interactive evaluation, multiline input,
history support, and runtime safety limits for controlled execution.
Also contains optional memory monitoring integrations when available.
"""

import sys
import re
import io
import os
from pathlib import Path

if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(50_000)

if hasattr(sys, "setrecursionlimit"):
    sys.setrecursionlimit(20_000)

from gladlang.core.util.global_scope import get_fresh_global_scope
from gladlang.core.util.memory import set_memory_limit
from gladlang.core.util.runner import run
from gladlang.core.util.repl_helpers import is_complete
from gladlang.runtime.context import Context
from gladlang.version import __version__


def main():
    MAX_MEMORY_MB = 512
    MAX_INSTRUCTIONS = int(sys.maxsize)
    MAX_SOURCE_BYTES = 1_000_000
    MAX_REPL_BUFFER = 100_000

    set_memory_limit(MAX_MEMORY_MB)

    GLADLANG_VERSION = str(__version__)
    GLADLANG_HELP = f"""
Usage: gladlang [command] [filename/code] [args...]

Commands:
  <no arguments>           Start the interactive GladLang shell.
  [filename.glad]          Execute a GladLang script file.
  ["code string"]          Execute inline GladLang code directly.
  [filename.glad] [args]   Execute script and pass args to INPUT().
  ["code string"] [args]   Execute inline code and pass args to INPUT().
  -h, --help               Show this help message and exit.
  -v, --version            Show the interpreter version and exit.
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

                if len(full_text) > MAX_REPL_BUFFER:
                    sys.stdout.write(
                        "Error: Input buffer limit exceeded. Clearing buffer.\n"
                    )
                    full_text = ""
                    continue

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
                    elif result is not None:
                        non_comment_lines = [
                            ln
                            for ln in full_text.splitlines()
                            if re.sub(r"#.*", "", ln).strip()
                        ]

                        if not non_comment_lines:
                            pass
                        else:
                            is_single_line = len(non_comment_lines) == 1
                            if not is_single_line:
                                pass
                            else:
                                sole = re.sub(r"#.*", "", non_comment_lines[0]).strip()
                                STATEMENT_PREFIXES = (
                                    "LET ",
                                    "LET[",
                                    "FINAL ",
                                    "ENUM ",
                                    "DEF ",
                                    "CLASS ",
                                    "ENDDEF",
                                    "ENDCLASS",
                                    "ENDENUM",
                                    "ENDIF",
                                    "ENDWHILE",
                                    "ENDFOR",
                                    "ENDTRY",
                                    "ENDSWITCH",
                                    "IF ",
                                    "ELSE",
                                    "WHILE ",
                                    "FOR ",
                                    "SWITCH ",
                                    "TRY",
                                    "THROW ",
                                    "RETURN",
                                    "BREAK",
                                    "CONTINUE",
                                    "PRINT",
                                    "PRINTLN",
                                    "PUBLIC ",
                                    "PRIVATE ",
                                    "PROTECTED ",
                                    "STATIC ",
                                    "SUPER",
                                )

                                is_assignment = bool(
                                    re.match(
                                        r"^[A-Za-z_][A-Za-z0-9_.]*(\s*\[.+?\])*\s*(\+|-|\*|/|%|\*\*|//|&|\||\^|<<|>>)?=(?!=)",
                                        sole,
                                    )
                                )

                                is_void_call = bool(
                                    re.match(
                                        r"^[A-Za-z_][A-Za-z0-9_.]*(\s*\[.+?\])*\s*\(",
                                        sole,
                                    )
                                )

                                is_increment = bool(
                                    re.match(
                                        r"^(\+\+|--)?[A-Za-z_][A-Za-z0-9_.]*(\s*\[.+?\])*\s*(\+\+|--)?$",
                                        sole,
                                    )
                                )

                                is_statement = any(
                                    sole.startswith(p) for p in STATEMENT_PREFIXES
                                )

                                if (
                                    not is_statement
                                    and not is_assignment
                                    and not is_void_call
                                    and not is_increment
                                ):
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

        if arg == "--help" or arg == "-h":
            sys.stdout.write(GLADLANG_HELP + "\n")

        elif arg == "--version" or arg == "-v":
            sys.stdout.write(f"GladLang v{GLADLANG_VERSION}\n")

        else:
            arg_input = arg
            script_args = sys.argv[2:]
            try:
                original_stdin = sys.stdin
                try:
                    if script_args:
                        sys.stdin = io.StringIO("\n".join(script_args) + "\n")

                    is_file = False
                    resolved = None
                    try:
                        candidate = Path(arg_input)
                        allowed_root = Path.cwd().resolve()
                        strict_path = candidate.resolve(strict=False)
                        if not strict_path.is_relative_to(allowed_root):
                            raise PermissionError(f"Access denied: '{arg_input}'")

                        try:
                            O_NOFOLLOW = os.O_NOFOLLOW
                            fd = os.open(str(candidate), os.O_RDONLY | O_NOFOLLOW)
                        except AttributeError:
                            fd = os.open(str(candidate), os.O_RDONLY)

                        with os.fdopen(fd, "r", encoding="utf-8") as f:
                            text = f.read()

                        is_file = True
                        resolved = candidate.resolve()
                    except (OSError, PermissionError) as e:
                        sys.stderr.write(f"Error accessing file: {e}\n")
                        sys.exit(1)

                    if is_file or arg_input.endswith(".glad"):
                        path_to_read = (
                            resolved if resolved else Path(arg_input).resolve()
                        )

                        if not path_to_read.suffix == ".glad" and not is_file:
                            sys.stderr.write(
                                f"File must have .glad extension: '{arg_input}'\n"
                            )
                            sys.exit(1)

                        if not is_file:
                            file_size = path_to_read.stat().st_size
                            if file_size > MAX_SOURCE_BYTES:
                                sys.stderr.write(
                                    f"File too large: '{arg_input}' ({file_size:,} bytes). Maximum allowed: {MAX_SOURCE_BYTES:,} bytes.\n"
                                )
                                sys.exit(1)

                            try:
                                text = path_to_read.read_text(encoding="utf-8")
                            except UnicodeDecodeError:
                                sys.stderr.write(
                                    f"Encoding error: '{arg_input}' is not valid UTF-8. Save the file as UTF-8 and try again.\n"
                                )
                                sys.exit(1)
                            except Exception as e:
                                sys.stderr.write(f"An unexpected error occurred: {e}\n")
                                sys.exit(1)

                        source_name = str(path_to_read)
                    else:
                        text = arg_input
                        source_name = "<cmdline>"

                    result, error = run(
                        source_name, text, instruction_limit=MAX_INSTRUCTIONS
                    )

                    if error:
                        sys.stderr.write(error.as_string() + "\n")

                finally:
                    sys.stdin = original_stdin

            except MemoryError:
                sys.stderr.write("System Error: Memory Limit Exceeded\n")
            except FileNotFoundError:
                sys.stderr.write(f"File not found: '{arg_input}'\n")
            except Exception as e:
                sys.stderr.write(f"An unexpected error occurred: {e}\n")

    else:
        sys.stdout.write("Error: Invalid arguments.\n")
        sys.stdout.write(GLADLANG_HELP + "\n")
