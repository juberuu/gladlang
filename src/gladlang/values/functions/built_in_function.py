"""BuiltInFunction – implements native functions like PRINTLN, INPUT, LEN, etc."""

import sys
import math
from gladlang.core.errors import RTError
from gladlang.runtime.rt_result import RTResult
from gladlang.values.functions.base_function import BaseFunction
from gladlang.values.primitives.number import Number
from gladlang.values.primitives.string import String
from gladlang.values.primitives.list import List
from gladlang.values.primitives.dict import Dict


class BuiltInFunction(BaseFunction):
    __slots__ = ()

    def __init__(self, name):
        super().__init__(name)

    def execute(self, args, interpreter):
        res = RTResult()

        if self.name == "INPUT":
            if len(args) > 1:
                return res.failure(
                    RTError(
                        self.pos_start,
                        self.pos_end,
                        "INPUT takes at most 1 argument",
                        self.context,
                    )
                )

            prompt = ""
            if len(args) == 1:
                prompt = str(args[0])

            if prompt:
                sys.stdout.write(prompt)
                sys.stdout.flush()

            text = sys.stdin.readline()
            if text == "":
                return res.failure(
                    RTError(
                        self.pos_start,
                        self.pos_end,
                        "INPUT: end of file reached (no input available)",
                        self.context,
                    )
                )

            text = text.rstrip("\n")

            return res.success(String(text))

        elif self.name == "STR":
            res.register(self.check_args(["value"], args))
            if res.error:
                return res

            val = args[0]

            if isinstance(val, String):
                return res.success(String(val.value))

            return res.success(String(str(val)))

        elif self.name == "INT":
            res.register(self.check_args(["value"], args))
            if res.error:
                return res

            arg = args[0]

            if not isinstance(arg, (Number, String)):
                return res.failure(
                    RTError(
                        self.pos_start,
                        self.pos_end,
                        f"Argument for INT must be a Number or String, got {type(arg).__name__}",
                        self.context,
                    )
                )

            try:
                if isinstance(arg, Number):
                    val = int(arg.value)
                else:
                    try:
                        val = int(arg.value)
                    except ValueError:
                        val = int(float(arg.value))

            except (ValueError, OverflowError):
                return res.failure(
                    RTError(
                        self.pos_start,
                        self.pos_end,
                        f"Cannot convert '{arg.value}' to INT",
                        self.context,
                    )
                )

            return res.success(Number(val))

        elif self.name == "FLOAT":
            res.register(self.check_args(["value"], args))
            if res.error:
                return res

            arg = args[0]
            if not isinstance(arg, (Number, String)):
                return res.failure(
                    RTError(
                        self.pos_start,
                        self.pos_end,
                        f"Argument for FLOAT must be a Number or String, got {type(arg).__name__}",
                        self.context,
                    )
                )

            try:
                val = float(arg.value)
            except ValueError:
                return res.failure(
                    RTError(
                        self.pos_start,
                        self.pos_end,
                        f"Cannot convert '{arg.value}' to FLOAT",
                        self.context,
                    )
                )

            if math.isinf(val) or math.isnan(val):
                return res.failure(
                    RTError(
                        self.pos_start,
                        self.pos_end,
                        f"FLOAT: result is not a finite number (got '{arg.value}')",
                        self.context,
                    )
                )

            return res.success(Number(val))

        elif self.name == "BOOL":
            res.register(self.check_args(["value"], args))
            if res.error:
                return res

            return res.success(Number(1) if args[0].is_true() else Number(0))

        elif self.name == "LEN":
            res.register(self.check_args(["value"], args))
            if res.error:
                return res

            arg = args[0]
            if isinstance(arg, String):
                return res.success(Number(len(arg.value)))
            elif isinstance(arg, List):
                return res.success(Number(len(arg.elements)))
            elif isinstance(arg, Dict):
                return res.success(Number(len(arg.elements)))
            elif isinstance(arg, Number):
                return res.failure(
                    RTError(
                        self.pos_start,
                        self.pos_end,
                        "LEN is not defined for Number, use STR(n) first if you want the digit count",
                        self.context,
                    )
                )
            else:
                from gladlang.values.functions.function import Function
                from gladlang.values.functions.function_group import FunctionGroup
                from gladlang.values.functions.bound_method import BoundMethod
                from gladlang.values.classes.class_ import Class

                if isinstance(
                    arg, (Function, FunctionGroup, BoundMethod, BuiltInFunction, Class)
                ):
                    return res.failure(
                        RTError(
                            self.pos_start,
                            self.pos_end,
                            f"LEN is not defined for type '{type(arg).__name__}'",
                            self.context,
                        )
                    )

                return res.failure(
                    RTError(
                        self.pos_start,
                        self.pos_end,
                        f"LEN is not supported for type '{type(arg).__name__}'",
                        self.context,
                    )
                )

        return res.failure(
            RTError(
                self.pos_start,
                self.pos_end,
                f"Unknown built-in function '{self.name}'",
                self.context,
            )
        )

    def copy(self):
        copy = BuiltInFunction(self.name)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self):
        return f"<built-in function {self.name}>"
