"""REPL helpers – string stripping and code completion detection for interactive shell."""

import re


def strip_double_quoted(text):
    result = []
    i = 0
    n = len(text)

    while i < n:
        if text[i] == '"':
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                elif text[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
        else:
            result.append(text[i])
            i += 1

    return "".join(result)


def is_complete(text):
    temp_text = re.sub(r'""".*?"""', "", text, flags=re.DOTALL)
    if temp_text.count('"""') % 2 != 0:
        return False

    temp_text = re.sub(r"`(?:\\\\.|[^`\\\\])*`", "", temp_text, flags=re.DOTALL)
    if temp_text.count("`") % 2 != 0:
        return False

    stripped = strip_double_quoted(temp_text)
    comment_free_lines = []

    for line in stripped.split("\n"):
        if "#" in line:
            line = line[: line.index("#")]

        comment_free_lines.append(line)

    stripped = "\n".join(comment_free_lines)

    if stripped.count('"') % 2 != 0:
        return False

    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0
    keyword_depth = 0

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

    neutral_keys = {"ELSE", "CATCH", "FINALLY"}

    i = 0
    n = len(stripped)
    while i < n:
        ch = stripped[i]

        if ch == "(":
            paren_depth += 1
            i += 1
            continue
        elif ch == ")":
            paren_depth = max(0, paren_depth - 1)
            i += 1
            continue
        elif ch == "[":
            bracket_depth += 1
            i += 1
            continue
        elif ch == "]":
            bracket_depth = max(0, bracket_depth - 1)
            i += 1
            continue
        elif ch == "{":
            brace_depth += 1
            i += 1
            continue
        elif ch == "}":
            brace_depth = max(0, brace_depth - 1)
            i += 1
            continue

        inside_comprehension = bracket_depth > 0 or brace_depth > 0

        if not inside_comprehension and stripped[i].isalpha():

            matched_neutral = False
            for kw in neutral_keys:
                if stripped.startswith(kw, i) and (
                    i + len(kw) == n or not stripped[i + len(kw)].isalpha()
                ):
                    after = i + len(kw)
                    while after < n and stripped[after] == " ":
                        after += 1
                    if (
                        kw == "ELSE"
                        and stripped.startswith("IF", after)
                        and (after + 2 == n or not stripped[after + 2].isalpha())
                    ):
                        i = after + 2
                    else:
                        i = after
                    matched_neutral = True
                    break

            if matched_neutral:
                continue

            matched_end = False
            for kw in end_keys:
                if stripped.startswith(kw, i) and (
                    i + len(kw) == n or not stripped[i + len(kw)].isalpha()
                ):
                    keyword_depth -= 1
                    i += len(kw)
                    matched_end = True
                    break

            if matched_end:
                continue

            matched_start = False
            for kw in start_keys:
                if stripped.startswith(kw, i) and (
                    i + len(kw) == n or not stripped[i + len(kw)].isalpha()
                ):
                    keyword_depth += 1
                    i += len(kw)
                    matched_start = True
                    break

            if matched_start:
                continue

        i += 1

    return (
        paren_depth == 0
        and bracket_depth == 0
        and brace_depth == 0
        and keyword_depth <= 0
    )
