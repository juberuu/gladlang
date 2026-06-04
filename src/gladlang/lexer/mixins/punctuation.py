"""Single‑character punctuation tokens (handled inline in base.make_tokens).

This mixin is kept as a placeholder for potential future extension.
All punctuation tokens (parentheses, braces, brackets, commas, dots,
colons, semicolons, question marks) are emitted directly in the main
lexing loop in LexerBase. No additional methods are required here.
"""


class LexerPunctuation:
    pass
