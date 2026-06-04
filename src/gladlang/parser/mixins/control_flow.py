"""Switch and try/catch/finally statements."""

from gladlang.core.constants import GL_KEYWORD, GL_COMMA, GL_COLON, GL_IDENTIFIER
from gladlang.core.errors import InvalidSyntaxError
from gladlang.parser.ast import SwitchNode, TryCatchNode
from gladlang.parser.parse_result import ParseResult


class ParserControlFlow:
    def switch_expr(self):
        res = ParseResult()

        switch_value = res.register(self.expr())
        if res.error:
            return res

        cases = []
        default_case = None

        while self.current_tok.matches(GL_KEYWORD, "CASE"):
            res.register_advancement()
            self.advance()

            case_conditions = [res.register(self.expr())]
            if res.error:
                return res

            while self.current_tok.type == GL_COMMA:
                res.register_advancement()
                self.advance()
                case_conditions.append(res.register(self.expr()))
                if res.error:
                    return res

            if self.current_tok.type == GL_COLON:
                res.register_advancement()
                self.advance()

            body = res.register(self.statement_list(("CASE", "DEFAULT", "ENDSWITCH")))
            if res.error:
                return res

            cases.append((case_conditions, body))

        if self.current_tok.matches(GL_KEYWORD, "DEFAULT"):
            res.register_advancement()
            self.advance()

            if self.current_tok.type == GL_COLON:
                res.register_advancement()
                self.advance()

            default_case = res.register(self.statement_list(("ENDSWITCH",)))
            if res.error:
                return res

        if not self.current_tok.matches(GL_KEYWORD, "ENDSWITCH"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected 'ENDSWITCH'",
                )
            )

        res.register_advancement()
        self.advance()

        return res.success(SwitchNode(switch_value, cases, default_case))

    def try_expr(self):
        res = ParseResult()

        if not self.current_tok.matches(GL_KEYWORD, "TRY"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected 'TRY'",
                )
            )

        try_pos_start = self.current_tok.pos_start.copy()
        res.register_advancement()
        self.advance()

        try_body = res.register(self.statement_list(("CATCH", "FINALLY", "ENDTRY")))
        if res.error:
            return res

        catch_var = None
        catch_body = None
        finally_body = None

        if self.current_tok.matches(GL_KEYWORD, "CATCH"):
            res.register_advancement()
            self.advance()

            if self.current_tok.type == GL_IDENTIFIER:
                catch_var = self.current_tok
                res.register_advancement()
                self.advance()

            catch_body = res.register(self.statement_list(("FINALLY", "ENDTRY")))
            if res.error:
                return res

        if self.current_tok.matches(GL_KEYWORD, "FINALLY"):
            res.register_advancement()
            self.advance()
            finally_body = res.register(self.statement_list(("ENDTRY",)))
            if res.error:
                return res

        if not self.current_tok.matches(GL_KEYWORD, "ENDTRY"):
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected 'ENDTRY'",
                )
            )

        res.register_advancement()
        self.advance()

        return res.success(
            TryCatchNode(
                try_body,
                catch_var,
                catch_body,
                finally_body,
                try_pos_start,
                self.current_tok.pos_start.copy(),
            )
        )
