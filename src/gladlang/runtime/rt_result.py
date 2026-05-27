"""RTResult – propagates return, break, continue, and error signals during interpretation."""


class RTResult:
    __slots__ = (
        "value",
        "error",
        "return_value",
        "should_return",
        "should_break",
        "should_continue",
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.value = None
        self.error = None
        self.return_value = None
        self.should_return = False
        self.should_break = False
        self.should_continue = False

        return self

    def register(self, res):
        if res.error is None and not (
            res.should_return or res.should_break or res.should_continue
        ):
            return res.value

        if res.error:
            self.error = res.error

        if res.should_return:
            self.return_value = res.return_value
            self.should_return = True

        if res.should_break:
            self.should_break = True

        if res.should_continue:
            self.should_continue = True

        return res.value

    def success(self, value):
        self.value = value
        return self

    def success_return(self, value):
        self.return_value = value
        self.should_return = True
        return self

    def success_break(self):
        self.should_break = True
        return self

    def success_continue(self):
        self.should_continue = True
        return self

    def failure(self, error):
        self.error = error
        return self
