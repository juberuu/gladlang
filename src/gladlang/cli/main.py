"""GladLang command-line interface and interactive REPL.

Provides script execution, interactive evaluation, multiline input,
history support, runtime safety limits, and drag-and-drop file loading.
Also contains optional memory monitoring integrations when available.
"""

import sys
import re
import io
import os
import shlex
import threading
from pathlib import Path

from gladlang.core.util.settings import Settings

if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(Settings.MAX_INT_STR_DIGITS)

if hasattr(sys, "setrecursionlimit"):
    sys.setrecursionlimit(Settings.PYTHON_RECURSION_LIMIT)

from gladlang.core.util.global_scope import get_fresh_global_scope
from gladlang.core.util.memory import set_memory_limit
from gladlang.core.util.runner import run
from gladlang.core.util.repl_helpers import is_complete
from gladlang.core.util.terminal import set_terminal_title
from gladlang.runtime.context import Context


def main():
    set_memory_limit(Settings.MAX_MEMORY_MB)

    threading.Thread(
        target=set_terminal_title, args=(Settings.TITLE,), daemon=True
    ).start()

    if len(sys.argv) == 1:
        sys.stdout.write(f"Welcome to GladLang (v{Settings.VERSION})\n")
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

                raw_line = line.strip()
                try:
                    tokens = shlex.split(raw_line, posix=False)
                except ValueError:
                    tokens = raw_line.split()

                first_token = tokens[0].strip("'\"") if tokens else ""
                extra_tokens = tokens[1:] if len(tokens) > 1 else []

                auto_confirm = any(t.lower() in ("-y", "-yes") for t in extra_tokens)
                auto_deny = any(t.lower() in ("-n", "-no") for t in extra_tokens)

                drop_args = [t for t in extra_tokens if not t.lower().startswith("-")]
                stripped_line = first_token

                if (
                    not full_text
                    and stripped_line.endswith(".glad")
                    and "\n" not in stripped_line
                ):
                    drop_path = Path(stripped_line)

                    if drop_path.is_symlink():
                        sys.stdout.write(
                            f"Access denied: '{stripped_line}' is a symbolic link\n"
                        )
                        continue

                    try:
                        strict_path = drop_path.resolve(strict=False)

                        try:
                            O_NOFOLLOW = os.O_NOFOLLOW
                            fd = os.open(str(strict_path), os.O_RDONLY | O_NOFOLLOW)
                        except AttributeError:
                            fd = os.open(str(strict_path), os.O_RDONLY)

                        file_size = os.fstat(fd).st_size
                        if file_size > Settings.MAX_SOURCE_BYTES:
                            os.close(fd)
                            sys.stdout.write(
                                f"Error: File too large ({file_size:,} bytes). "
                                f"Maximum allowed: {Settings.MAX_SOURCE_BYTES:,} bytes.\n"
                            )
                            continue

                        try:
                            with os.fdopen(fd, "r", encoding="utf-8") as f:
                                dropped_source = f.read()
                        except UnicodeDecodeError:
                            sys.stdout.write(
                                f"Error: '{stripped_line}' is not valid UTF-8. "
                                "Save the file as UTF-8 and try again.\n"
                            )
                            continue

                        if auto_deny:
                            sys.stdout.write("Cancelled by user.\n")
                            continue

                        if not auto_confirm:
                            sys.stdout.write(
                                f"Run '{drop_path.name}' ({file_size:,} bytes)? [y/n] "
                            )
                            sys.stdout.flush()

                            confirm = sys.stdin.readline().strip().lower()
                            if confirm != "y":
                                sys.stdout.write("Cancelled by user.\n")
                                continue

                        sys.stdout.write(f"Running '{drop_path.name}'...\n")

                        original_stdin = sys.stdin
                        try:
                            if drop_args:
                                sys.stdin = io.StringIO("\n".join(drop_args) + "\n")

                            repl_context.symbol_table = get_fresh_global_scope()

                            result, error = run(
                                str(strict_path),
                                dropped_source,
                                repl_context,
                                instruction_limit=Settings.MAX_INSTRUCTIONS,
                            )
                        finally:
                            sys.stdin = original_stdin

                        if error:
                            sys.stdout.write(error.as_string() + "\n")

                        continue

                    except FileNotFoundError:
                        sys.stdout.write(f"Error: File not found: '{stripped_line}'\n")
                        continue
                    except PermissionError as e:
                        sys.stdout.write(f"Error: {e}\n")
                        continue
                    except OSError as e:
                        sys.stdout.write(f"Error accessing file: {e}\n")
                        continue

                full_text += line + "\n"

                if len(full_text) > Settings.MAX_REPL_BUFFER:
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
                        instruction_limit=Settings.MAX_INSTRUCTIONS,
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
            sys.stdout.write(f"{Settings.HELP}\n")

        elif arg == "--version" or arg == "-v":
            sys.stdout.write(f"GladLang v{Settings.VERSION}\n")

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
                        strict_path = candidate.resolve(strict=False)

                        try:
                            O_NOFOLLOW = os.O_NOFOLLOW
                            fd = os.open(str(strict_path), os.O_RDONLY | O_NOFOLLOW)
                        except AttributeError:
                            fd = os.open(str(strict_path), os.O_RDONLY)

                        file_size = os.fstat(fd).st_size
                        if file_size > Settings.MAX_SOURCE_BYTES:
                            os.close(fd)
                            sys.stderr.write(
                                f"File too large: '{arg_input}' ({file_size:,} bytes). "
                                f"Maximum allowed: {Settings.MAX_SOURCE_BYTES:,} bytes.\n"
                            )
                            sys.exit(1)

                        with os.fdopen(fd, "r", encoding="utf-8") as f:
                            text = f.read()

                        is_file = True
                        resolved = candidate.resolve()
                    except (OSError, PermissionError) as e:
                        sys.stderr.write(f"Error accessing file: {e}\n")
                        sys.exit(1)

                    if is_file or arg_input.endswith(".glad"):
                        candidate_path = Path(arg_input)
                        if candidate_path.is_symlink():
                            sys.stderr.write(
                                f"Access denied: '{arg_input}' is a symbolic link\n"
                            )
                            sys.exit(1)

                        path_to_read = (
                            resolved if resolved else candidate_path.resolve()
                        )

                        if not path_to_read.suffix == ".glad" and not is_file:
                            sys.stderr.write(
                                f"File must have .glad extension: '{arg_input}'\n"
                            )
                            sys.exit(1)

                        try:
                            O_NOFOLLOW = os.O_NOFOLLOW
                            fd = os.open(str(path_to_read), os.O_RDONLY | O_NOFOLLOW)
                        except AttributeError:
                            fd = os.open(str(path_to_read), os.O_RDONLY)

                        file_size = os.fstat(fd).st_size
                        if file_size > Settings.MAX_SOURCE_BYTES:
                            os.close(fd)
                            sys.stderr.write(
                                f"File too large: '{arg_input}' ({file_size:,} bytes). Maximum allowed: {Settings.MAX_SOURCE_BYTES:,} bytes.\n"
                            )
                            sys.exit(1)

                        try:
                            with os.fdopen(fd, "r", encoding="utf-8") as f:
                                text = f.read()
                        except UnicodeDecodeError:
                            sys.stderr.write(
                                f"Encoding error: '{arg_input}' is not valid UTF-8. Save the file as UTF-8 and try again.\n"
                            )
                            sys.exit(1)

                        source_name = str(path_to_read)
                    else:
                        text = arg_input
                        source_name = "<cmdline>"

                    result, error = run(
                        source_name, text, instruction_limit=Settings.MAX_INSTRUCTIONS
                    )

                    if error:
                        sys.stderr.write(f"{error.as_string()}\n")

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
        sys.stdout.write(Settings.HELP + "\n")
