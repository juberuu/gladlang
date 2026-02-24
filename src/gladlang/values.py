import sys
from .errors import RTError
from .runtime import SymbolTable, Context, RTResult
from .constants import GL_IDENTIFIER
from .lexer import Token
from .nodes import *


class Value:
    def __init__(self):
        self.set_pos()
        self.set_context()

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def added_to(self, other):
        return None, self.illegal_operation(other)

    def subbed_by(self, other):
        return None, self.illegal_operation(other)

    def multed_by(self, other):
        return None, self.illegal_operation(other)

    def dived_by(self, other):
        return None, self.illegal_operation(other)

    def modded_by(self, other):
        return None, self.illegal_operation(other)

    def floordived_by(self, other):
        return None, self.illegal_operation(other)

    def powed_by(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_eq(self, other, visited=None):
        return None, self.illegal_operation(other)

    def get_comparison_ne(self, other):
        result, error = self.get_comparison_eq(other)
        if error:
            return None, error
        if result.is_true():
            return Number(0).set_context(self.context), None
        else:
            return Number(1).set_context(self.context), None

    def get_comparison_lt(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_gt(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_lte(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_gte(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_is(self, other):
        return Number(1 if self is other else 0).set_context(self.context), None

    def get_comparison_instanceof(self, other):
        if isinstance(other, Type):
            if other.name == "Number" and isinstance(self, Number):
                return Number.true.copy(), None
            if other.name == "String" and isinstance(self, String):
                return Number.true.copy(), None
            if other.name == "List" and isinstance(self, List):
                return Number.true.copy(), None
            if other.name == "Dict" and isinstance(self, Dict):
                return Number.true.copy(), None
            if other.name == "Function" and isinstance(self, BaseFunction):
                return Number.true.copy(), None
            if other.name == "Object":
                return Number.true.copy(), None
            return Number.false.copy(), None

        if isinstance(other, Class):
            return Number.false.copy(), None

        return None, RTError(
            self.pos_start,
            self.pos_end,
            "Right operand of INSTANCEOF must be a Class or Type",
            self.context,
        )

    def anded_by(self, other):
        is_true = self.is_true() and other.is_true()
        return Number(1 if is_true else 0).set_context(self.context), None

    def ored_by(self, other):
        is_true = self.is_true() or other.is_true()
        return Number(1 if is_true else 0).set_context(self.context), None

    def notted(self):
        return None, self.illegal_operation()

    def execute(self, args, interpreter=None):
        return RTResult().failure(self.illegal_operation())

    def get_attr(self, name_tok):
        return None, self.illegal_operation()

    def set_attr(self, name_tok, value, context=None, visibility=None, as_final=False):
        return None, self.illegal_operation()

    def get_element_at(self, index):
        return None, self.illegal_operation()

    def set_element_at(self, index, value):
        return None, self.illegal_operation()

    def is_true(self):
        return True

    def copy(self):
        raise Exception("No copy method defined")

    def bitted_and_by(self, other):
        return None, self.illegal_operation(other)

    def bitted_or_by(self, other):
        return None, self.illegal_operation(other)

    def bitted_xor_by(self, other):
        return None, self.illegal_operation(other)

    def lshifted_by(self, other):
        return None, self.illegal_operation(other)

    def rshifted_by(self, other):
        return None, self.illegal_operation(other)

    def bitted_not(self):
        return None, self.illegal_operation()

    def illegal_operation(self, other=None):
        if not other:
            other = self
        return RTError(self.pos_start, other.pos_end, "Illegal operation", self.context)


class Number(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def added_to(self, other):
        if isinstance(other, Number):
            return Number(self.value + other.value).set_context(self.context), None
        elif isinstance(other, String):
            return String(str(self.value) + other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def subbed_by(self, other):
        if isinstance(other, Number):
            return Number(self.value - other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def multed_by(self, other):
        if isinstance(other, Number):
            return Number(self.value * other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def dived_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RTError(
                    other.pos_start, other.pos_end, "Division by zero", self.context
                )
            return Number(self.value / other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def modded_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RTError(
                    other.pos_start, other.pos_end, "Division by zero", self.context
                )
            return Number(self.value % other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def floordived_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RTError(
                    other.pos_start, other.pos_end, "Division by zero", self.context
                )
            return Number(self.value // other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_is(self, other):
        return Number(1 if self is other else 0).set_context(self.context), None

    def powed_by(self, other):
        if isinstance(other, Number):
            if other.value > 10000:
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    "Exponent too large (limit: 10000)",
                    self.context,
                )
            try:
                result = self.value**other.value
            except (ValueError, ZeroDivisionError) as e:
                return None, RTError(
                    other.pos_start, other.pos_end, str(e), self.context
                )

            if isinstance(result, complex):
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    "Math domain error: result is complex",
                    self.context,
                )
            import math

            if isinstance(result, float) and math.isnan(result):
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    "Math domain error: result is NaN",
                    self.context,
                )
            return Number(result).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_eq(self, other, visited=None):
        if isinstance(other, Number):
            return (
                Number(int(self.value == other.value)).set_context(self.context),
                None,
            )
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_ne(self, other):
        if isinstance(other, Number):
            return (
                Number(int(self.value != other.value)).set_context(self.context),
                None,
            )
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_lt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value < other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_gt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value > other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_lte(self, other):
        if isinstance(other, Number):
            return (
                Number(int(self.value <= other.value)).set_context(self.context),
                None,
            )
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_gte(self, other):
        if isinstance(other, Number):
            return (
                Number(int(self.value >= other.value)).set_context(self.context),
                None,
            )
        else:
            return None, Value.illegal_operation(self, other)

    def anded_by(self, other):
        if isinstance(other, Number):
            return (
                Number(int(self.value and other.value)).set_context(self.context),
                None,
            )
        else:
            return None, Value.illegal_operation(self, other)

    def ored_by(self, other):
        if isinstance(other, Number):
            return (
                Number(int(self.value or other.value)).set_context(self.context),
                None,
            )
        else:
            return None, Value.illegal_operation(self, other)

    def notted(self):
        return Number(1 if self.value == 0 else 0).set_context(self.context), None

    def bitted_and_by(self, other):
        if isinstance(other, Number):
            res = (int(self.value) & int(other.value)) & 0xFFFFFFFF
            return Number(res).set_context(self.context), None
        return None, Value.illegal_operation(self, other)

    def bitted_or_by(self, other):
        if isinstance(other, Number):
            res = (int(self.value) | int(other.value)) & 0xFFFFFFFF
            return Number(res).set_context(self.context), None
        return None, Value.illegal_operation(self, other)

    def bitted_xor_by(self, other):
        if isinstance(other, Number):
            res = (int(self.value) ^ int(other.value)) & 0xFFFFFFFF
            return Number(res).set_context(self.context), None
        return None, Value.illegal_operation(self, other)

    def lshifted_by(self, other):
        if isinstance(other, Number):
            try:
                result = (int(self.value) << int(other.value)) & 0xFFFFFFFF
                return Number(result).set_context(self.context), None
            except ValueError:
                return None, RTError(
                    other.pos_start, other.pos_end, "Negative shift count", self.context
                )
        return None, Value.illegal_operation(self, other)

    def bitted_not(self):
        return Number((~int(self.value)) & 0xFFFFFFFF).set_context(self.context), None

    def rshifted_by(self, other):
        if isinstance(other, Number):
            return (
                Number(int(self.value) >> int(other.value)).set_context(self.context),
                None,
            )
        return None, Value.illegal_operation(self, other)

    def is_true(self):
        return self.value != 0

    def copy(self):
        copy = Number(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __repr__(self):
        return str(self.value)


Number.false = Number(0)
Number.true = Number(1)
Number.null = Number.false.copy()


class String(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def added_to(self, other):
        if isinstance(other, String):
            return String(self.value + other.value).set_context(self.context), None
        elif isinstance(other, Number):
            return String(self.value + str(other.value)).set_context(self.context), None
        else:
            return None, self.illegal_operation(other)

    def get_comparison_eq(self, other, visited=None):
        if isinstance(other, String):
            return (
                Number(int(self.value == other.value)).set_context(self.context),
                None,
            )
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_ne(self, other):
        if isinstance(other, String):
            return (
                Number(int(self.value != other.value)).set_context(self.context),
                None,
            )
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_lt(self, other):
        if isinstance(other, String):
            return Number(int(self.value < other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_gt(self, other):
        if isinstance(other, String):
            return Number(int(self.value > other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_lte(self, other):
        if isinstance(other, String):
            return (
                Number(int(self.value <= other.value)).set_context(self.context),
                None,
            )
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_gte(self, other):
        if isinstance(other, String):
            return (
                Number(int(self.value >= other.value)).set_context(self.context),
                None,
            )
        else:
            return None, Value.illegal_operation(self, other)

    def get_element_at(self, index):
        if not isinstance(index, Number):
            return None, RTError(
                self.pos_start,
                self.pos_end,
                "String index must be a Number",
                self.context,
            )

        try:
            val = self.value[int(index.value)]
            return String(val).set_context(self.context), None
        except IndexError:
            return None, RTError(
                self.pos_start,
                self.pos_end,
                f"String index {index.value} out of bounds",
                self.context,
            )

    def is_true(self):
        return len(self.value) > 0

    def copy(self):
        copy = String(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __repr__(self):
        return self.value


class List(Value):
    MAX_LIST_SIZE = 1_000_000

    def __init__(self, elements):
        super().__init__()
        self.elements = elements

    def is_true(self):
        return len(self.elements) > 0

    def added_to(self, other):
        if isinstance(other, List):
            new_list = List(self.elements + other.elements)
            new_list.set_context(self.context)
            return new_list, None
        else:
            return None, self.illegal_operation(other)

    def multed_by(self, other):
        if isinstance(other, Number):
            result_len = len(self.elements) * int(other.value)
            if result_len > List.MAX_LIST_SIZE:
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    f"List repetition result ({result_len}) exceeds maximum allowed size ({List.MAX_LIST_SIZE})",
                    self.context,
                )
            new_list = List(self.elements * int(other.value))
            new_list.set_context(self.context)
            return new_list, None
        return None, self.illegal_operation(other)

    def get_element_at(self, index):
        if not isinstance(index, Number):
            return None, RTError(
                self.pos_start,
                self.pos_end,
                "List index must be a Number",
                self.context,
            )

        try:
            element = self.elements[int(index.value)]
            return element, None
        except IndexError:
            return None, RTError(
                self.pos_start,
                self.pos_end,
                f"List index {index.value} out of bounds",
                self.context,
            )

    def set_element_at(self, index, value):
        if not isinstance(index, Number):
            return None, RTError(
                self.pos_start,
                self.pos_end,
                "List index must be a Number",
                self.context,
            )

        try:
            self.elements[int(index.value)] = value
            return value, None
        except IndexError:
            return None, RTError(
                self.pos_start,
                self.pos_end,
                f"List index {index.value} out of bounds",
                self.context,
            )

    def get_comparison_eq(self, other, visited=None):
        if not isinstance(other, List):
            return None, Value.illegal_operation(self, other)

        if len(self.elements) != len(other.elements):
            return Number(0).set_context(self.context), None

        if visited is None:
            visited = set()

        pair = (id(self), id(other))
        if pair in visited:
            return Number(1).set_context(self.context), None

        visited.add(pair)

        try:
            for i in range(len(self.elements)):
                result, error = self.elements[i].get_comparison_eq(
                    other.elements[i], visited
                )
                if error:
                    return None, error
                if not result.is_true():
                    return Number(0).set_context(self.context), None
        finally:
            visited.remove(pair)

        return Number(1).set_context(self.context), None

    def get_comparison_ne(self, other):
        if not isinstance(other, List):
            return None, Value.illegal_operation(self, other)

        result, error = self.get_comparison_eq(other)
        if error:
            return None, error

        if result.is_true():
            return Number(0).set_context(self.context), None
        else:
            return Number(1).set_context(self.context), None

    def copy(self):
        copy = List([e.copy() for e in self.elements])
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __repr__(self):
        return self.to_string([])

    def to_string(self, visited):
        if self in visited:
            return "[...]"
        visited.append(self)
        s = f'[{", ".join([x.to_string(visited) if isinstance(x, (List, Dict)) else repr(x) for x in self.elements])}]'
        visited.pop()
        return s


class Dict(Value):
    def __init__(self, elements):
        super().__init__()
        self.elements = elements

    def is_true(self):
        return len(self.elements) > 0

    def copy(self):
        copy = Dict({k: v.copy() for k, v in self.elements.items()})
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def added_to(self, other):
        if isinstance(other, Dict):
            new_dict = self.copy()
            new_dict.elements.update(other.elements)
            return new_dict, None
        return None, self.illegal_operation(other)

    def get_element_at(self, key):
        if not isinstance(key, (Number, String)):
            return None, RTError(
                self.pos_start,
                self.pos_end,
                "Key must be a Number or String",
                self.context,
            )

        val = self.elements.get(key.value)
        if val is None:
            return None, RTError(
                self.pos_start,
                self.pos_end,
                f"Key '{key.value}' not found",
                self.context,
            )
        return val, None

    def set_element_at(self, key, value):
        if not isinstance(key, (Number, String)):
            return None, RTError(
                self.pos_start,
                self.pos_end,
                "Key must be a Number or String",
                self.context,
            )

        self.elements[key.value] = value
        return value, None

    def get_comparison_eq(self, other, visited=None):
        if not isinstance(other, Dict):
            return None, Value.illegal_operation(self, other)

        if len(self.elements) != len(other.elements):
            return Number(0).set_context(self.context), None

        if visited is None:
            visited = set()

        pair = (id(self), id(other))
        if pair in visited:
            return Number(1).set_context(self.context), None

        visited.add(pair)

        try:
            for key, value in self.elements.items():
                if key not in other.elements:
                    return Number(0).set_context(self.context), None

                other_val = other.elements[key]
                result, error = value.get_comparison_eq(other_val, visited)
                if error:
                    return None, error

                if not result.is_true():
                    return Number(0).set_context(self.context), None
        finally:
            visited.remove(pair)

        return Number(1).set_context(self.context), None

    def get_comparison_ne(self, other):
        if not isinstance(other, Dict):
            return None, Value.illegal_operation(self, other)

        result, error = self.get_comparison_eq(other)
        if error:
            return None, error

        if result.is_true():
            return Number(0).set_context(self.context), None
        else:
            return Number(1).set_context(self.context), None

    def __repr__(self):
        return self.to_string([])

    def to_string(self, visited):
        if self in visited:
            return "{...}"
        visited.append(self)
        kv_strings = []
        for key, value in self.elements.items():
            val_str = (
                value.to_string(visited)
                if isinstance(value, (List, Dict))
                else repr(value)
            )
            kv_strings.append(f"{repr(key)}: {val_str}")
        s = f"{{{', '.join(kv_strings)}}}"
        visited.pop()
        return s


class BaseFunction(Value):
    def __init__(self, name):
        super().__init__()
        self.name = name or "<anonymous>"

    def generate_new_context(self):
        new_context = Context(self.name, self.context, self.pos_start)
        new_context.symbol_table = SymbolTable(self.context.symbol_table)
        return new_context

    def get_comparison_eq(self, other, visited=None):
        if isinstance(other, BaseFunction):
            return Number(1 if self is other else 0).set_context(self.context), None
        return None, self.illegal_operation(other)

    def get_comparison_ne(self, other):
        if isinstance(other, BaseFunction):
            return Number(1 if self is not other else 0).set_context(self.context), None
        return None, self.illegal_operation(other)

    def check_args(self, arg_names, args):
        res = RTResult()
        if len(args) != len(arg_names):
            return res.failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    f"Incorrect argument count for '{self.name}'. Expected {len(arg_names)}, got {len(args)}",
                    self.context,
                )
            )
        return res.success(None)

    def populate_args(self, arg_names, args, new_context):
        for i in range(len(args)):
            new_context.symbol_table.set(arg_names[i], args[i])

    def check_and_populate_args(self, arg_names, args, new_context):
        res = RTResult()
        res.register(self.check_args(arg_names, args))
        if res.error:
            return res
        self.populate_args(arg_names, args, new_context)
        return res.success(None)

    def execute(self, args, interpreter):
        return RTResult().failure(
            RTError(
                self.pos_start,
                self.pos_end,
                "BaseFunction cannot be executed",
                self.context,
            )
        )

    def copy(self):
        raise Exception("Cannot copy a BaseFunction")

    def __repr__(self):
        return f"<function {self.name}>"


class Function(BaseFunction):
    def __init__(
        self,
        name,
        body_node,
        arg_name_toks,
        parent_context,
        visibility="PUBLIC",
        defining_class=None,
        is_static=False,
    ):
        super().__init__(name)
        self.body_node = body_node
        self.arg_name_toks = arg_name_toks
        self.arg_names = [tok.value for tok in arg_name_toks]
        self.context = parent_context
        self.visibility = visibility
        self.defining_class = defining_class
        self.is_static = is_static

    def execute(self, args, interpreter):
        res = RTResult()

        new_context = self.generate_new_context()

        new_context.active_class = self.defining_class

        if new_context.depth > 250:
            return res.failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "Recursion limit exceeded",
                    self.context,
                )
            )

        res.register(self.check_and_populate_args(self.arg_names, args, new_context))
        if res.error:
            return res

        value_result = interpreter.visit(self.body_node, new_context)

        if value_result.error:
            return value_result

        if value_result.should_return:
            return res.success(value_result.return_value)

        return res.success(value_result.value or Number.null.copy())

    def copy(self):
        copy = Function(
            self.name,
            self.body_node,
            self.arg_name_toks,
            self.context,
            self.visibility,
            self.defining_class,
            self.is_static,
        )

        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy


class FunctionGroup(BaseFunction):
    def __init__(self, name):
        super().__init__(name)
        self.functions = {}
        self.visibility = "PUBLIC"
        self.is_static = False
        self.defining_class = None

    def add_function(self, func):
        arity = len(func.arg_names)

        if arity in self.functions:
            return RTResult().failure(
                RTError(
                    func.pos_start,
                    func.pos_end,
                    f"Overload conflict: '{self.name}' already has a variant with {arity} argument(s)",
                    None,
                )
            )

        self.functions[arity] = func

        if len(self.functions) == 1:
            self.visibility = getattr(func, "visibility", "PUBLIC")
            self.is_static = getattr(func, "is_static", False)
            self.defining_class = getattr(func, "defining_class", None)
        else:
            if getattr(func, "visibility", "PUBLIC") != self.visibility:
                return RTResult().failure(
                    RTError(
                        func.pos_start,
                        func.pos_end,
                        f"All overloads of '{self.name}' must have the same visibility",
                        None,
                    )
                )

        return None

    def execute(self, args, interpreter):
        arity = len(args)
        if arity not in self.functions:
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    f"No variant of function '{self.name}' found that accepts {arity} arguments",
                    self.context,
                )
            )

        return self.functions[arity].execute(args, interpreter)

    def bind_to_instance(self, instance):
        return BoundMethod(self.name, self, instance)

    def copy(self):
        copy = FunctionGroup(self.name)
        copy.visibility = self.visibility
        copy.is_static = self.is_static
        copy.defining_class = self.defining_class

        for arity, func in self.functions.items():
            copy.functions[arity] = func.copy()
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __repr__(self):
        return f"<function group {self.name}>"


class Class(BaseFunction):
    def __init__(self, name, superclasses, methods, static_symbol_table=None, mro=None):
        super().__init__(name)
        self.superclasses = superclasses
        self.methods = methods
        self.static_symbol_table = (
            static_symbol_table if static_symbol_table else SymbolTable()
        )
        self.mro = mro if mro else [self]

    def instantiate(self, args, context=None, interpreter=None):
        res = RTResult()
        instance = Instance(self)

        constructor_name = None

        for cls in self.mro:
            if cls.name in cls.methods:
                constructor_name = cls.name
                break

        if constructor_name:
            fake_tok = Token(
                GL_IDENTIFIER, constructor_name, self.pos_start, self.pos_end
            )
            init_method, error = self.get_attr(fake_tok, context, allow_instance=True)

            if error:
                return res.failure(error)

            bound_init = init_method.copy().bind_to_instance(instance)
            res.register(bound_init.execute(args, interpreter))
            if res.error:
                return res
        else:
            if len(args) > 0:
                return res.failure(
                    RTError(
                        self.pos_start,
                        self.pos_end,
                        f"'{self.name}' does not have a constructor that accepts arguments",
                        self.context,
                    )
                )

        return res.success(instance)

    def execute(self, args, interpreter=None):
        return RTResult().failure(
            RTError(
                self.pos_start,
                self.pos_end,
                f"Class '{self.name}' must be instantiated using 'NEW'",
                self.context,
            )
        )

    def set_attr(self, name_tok, value, context=None, visibility=None, as_final=False):
        name = name_tok.value

        if visibility == "FINAL":
            visibility = "PUBLIC"
            as_final = True

        if as_final or visibility is not None:
            if name in self.static_symbol_table.symbols:
                return None, RTError(
                    name_tok.pos_start,
                    name_tok.pos_end,
                    f"Static field '{name}' is already defined",
                    context,
                )
            self.static_symbol_table.set(
                name, value, visibility=(visibility or "PUBLIC"), as_final=as_final
            )
            return value, None

        if self.static_symbol_table.get(name):
            if name in self.static_symbol_table.finals:
                return None, RTError(
                    name_tok.pos_start,
                    name_tok.pos_end,
                    f"Cannot reassign static constant '{name}'",
                    context,
                )
            err = self.static_symbol_table.update(name, value)
            if err:
                return None, RTError(name_tok.pos_start, name_tok.pos_end, err, context)
            return value, None

        return None, RTError(
            name_tok.pos_start,
            name_tok.pos_end,
            f"Class '{self.name}' has no static field '{name}'",
            self.context,
        )

    def get_attr(self, name_tok, context=None, allow_instance=False):
        method_name = name_tok.value

        for cls in self.mro:
            val = cls.static_symbol_table.get(method_name)
            if val is not None:
                visibility = cls.static_symbol_table.get_visibility(method_name)
                defining_class = cls

                if visibility == "PRIVATE":
                    if not context or context.active_class != defining_class:
                        return None, RTError(
                            name_tok.pos_start,
                            name_tok.pos_end,
                            f"Cannot access private static field '{method_name}'",
                            context,
                        )

                if visibility == "PROTECTED":
                    allowed = False
                    if context and context.active_class:
                        if (
                            defining_class in context.active_class.mro
                            or context.active_class in defining_class.mro
                        ):
                            allowed = True

                    if not allowed:
                        return None, RTError(
                            name_tok.pos_start,
                            name_tok.pos_end,
                            f"Cannot access protected static field '{method_name}'",
                            context,
                        )

                return val, None

            method = cls.methods.get(method_name)
            if method:
                visibility = method.visibility
                defining_class = method.defining_class

                if visibility == "PRIVATE":
                    if not context or context.active_class != defining_class:
                        return None, RTError(
                            name_tok.pos_start,
                            name_tok.pos_end,
                            f"Cannot access private method '{method_name}' via Class",
                            context,
                        )

                if visibility == "PROTECTED":
                    allowed = False
                    if context and context.active_class:
                        if defining_class in context.active_class.mro:
                            allowed = True

                    if not allowed:
                        return None, RTError(
                            name_tok.pos_start,
                            name_tok.pos_end,
                            f"Cannot access protected method '{method_name}' via Class",
                            context,
                        )

                if method.is_static:
                    return (
                        method.copy()
                        .set_context(self.context)
                        .set_pos(name_tok.pos_start, name_tok.pos_end),
                        None,
                    )

                if context:
                    instance = context.symbol_table.get("THIS")
                    if (
                        instance
                        and isinstance(instance, Instance)
                        and self in instance.class_ref.mro
                    ):
                        return method.copy().bind_to_instance(instance), None

                return method.copy(), None

        return None, RTError(
            name_tok.pos_start,
            name_tok.pos_end,
            f"Class '{self.name}' has no member '{method_name}'",
            self.context,
        )

    def copy(self):
        copy = Class(
            self.name,
            self.superclasses[:],
            {k: v.copy() for k, v in self.methods.items()},
            self.static_symbol_table.copy(),
            self.mro[:],
        )
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self):
        return f"<class {self.name}>"


class Instance(Value):
    def __init__(self, class_ref):
        super().__init__()
        self.class_ref = class_ref
        self.symbol_table = SymbolTable()

    def check_access(self, name_tok, visibility, defining_class, context):
        if visibility == "PUBLIC":
            return None

        if visibility == "PRIVATE":
            if not context or context.active_class != defining_class:
                return RTError(
                    name_tok.pos_start,
                    name_tok.pos_end,
                    f"Cannot access private member '{name_tok.value}'",
                    context,
                )

        if visibility == "PROTECTED":
            allowed = False
            if context and context.active_class:
                if (
                    defining_class in context.active_class.mro
                    or context.active_class in defining_class.mro
                ):
                    allowed = True
            if not allowed:
                return RTError(
                    name_tok.pos_start,
                    name_tok.pos_end,
                    f"Cannot access protected member '{name_tok.value}'",
                    context,
                )
        return None

    def get_attr(self, name_tok, context=None):
        name = name_tok.value

        if context and context.active_class:
            mangled_name = f"_{context.active_class.name}__{name}"
            val = self.symbol_table.get(mangled_name)
            if val:
                return val, None

        value = self.symbol_table.get(name)
        if value is not None:
            visibility = self.symbol_table.get_visibility(name)
            error = self.check_access(name_tok, visibility, self.class_ref, context)
            if error:
                return None, error
            return value, None

        member, error = self.class_ref.get_attr(name_tok, context, allow_instance=True)
        if error:
            return None, error

        if isinstance(member, BaseFunction):
            if isinstance(member, Function) and member.is_static:
                return member, None

            error = self.check_access(
                name_tok, member.visibility, member.defining_class, context
            )
            if error:
                return None, error

            bound_method = member.copy().bind_to_instance(self)
            return bound_method, None

        return member, None

    def set_attr(self, name_tok, value, context=None, visibility=None, as_final=False):
        name = name_tok.value

        if visibility == "FINAL":
            visibility = "PUBLIC"
            as_final = True

        mangled_name = None
        if context and context.active_class:
            mangled_name = f"_{context.active_class.name}__{name}"

        if visibility is not None or as_final:
            target_name = mangled_name if visibility == "PRIVATE" else name

            if target_name in self.symbol_table.symbols:
                return None, RTError(
                    name_tok.pos_start,
                    name_tok.pos_end,
                    f"Attribute '{name}' is already defined",
                    context,
                )

            self.symbol_table.set(
                target_name,
                value,
                visibility=(visibility or "PUBLIC"),
                as_final=as_final,
            )

            if visibility == "PRIVATE" and self.symbol_table.get(name):
                if name in self.symbol_table.finals:
                    return None, RTError(
                        name_tok.pos_start,
                        name_tok.pos_end,
                        f"Cannot shadow constant '{name}' with a private variable",
                        context,
                    )
                self.symbol_table.remove(name)

            return value, None

        if mangled_name and self.symbol_table.get(mangled_name):
            if mangled_name in self.symbol_table.finals:
                return None, RTError(
                    name_tok.pos_start,
                    name_tok.pos_end,
                    f"Cannot reassign constant '{name}'",
                    context,
                )
            self.symbol_table.set(mangled_name, value, visibility="PRIVATE")
            return value, None

        if self.symbol_table.get(name):
            current_vis = self.symbol_table.get_visibility(name)
            error = self.check_access(name_tok, current_vis, self.class_ref, context)
            if error:
                return None, error

            if name in self.symbol_table.finals:
                return None, RTError(
                    name_tok.pos_start,
                    name_tok.pos_end,
                    f"Cannot reassign constant '{name}'",
                    context,
                )

            self.symbol_table.set(name, value, visibility=current_vis)
            return value, None

        if self.class_ref.static_symbol_table.get(name):
            if name in self.class_ref.static_symbol_table.finals:
                return None, RTError(
                    name_tok.pos_start,
                    name_tok.pos_end,
                    f"Cannot shadow static constant '{name}' with an instance variable",
                    context,
                )

        self.symbol_table.set(name, value, visibility="PUBLIC")
        return value, None

    def get_comparison_eq(self, other, visited=None):
        if isinstance(other, Instance):
            return Number(1 if self is other else 0).set_context(self.context), None
        return None, self.illegal_operation(other)

    def get_comparison_ne(self, other):
        if isinstance(other, Instance):
            return Number(1 if self is not other else 0).set_context(self.context), None
        return None, self.illegal_operation(other)

    def get_comparison_instanceof(self, other):
        if isinstance(other, Class):
            is_instance = other in self.class_ref.mro
            return Number(1 if is_instance else 0).set_context(self.context), None

        if isinstance(other, Type):
            if other.name == "Object":
                return Number.true.copy(), None
            return Number.false.copy(), None

        return None, RTError(
            self.pos_start,
            self.pos_end,
            "Right operand of INSTANCEOF must be a Class or Type",
            self.context,
        )

    def copy(self):
        copy = Instance(self.class_ref)
        copy.symbol_table = self.symbol_table.copy()
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self):
        return f"<{self.class_ref.name} instance>"


class Super(Value):
    def __init__(self, instance, start_class):
        super().__init__()
        self.instance = instance
        self.start_class = start_class

    def get_attr(self, name_tok, context=None):
        method_name = name_tok.value
        mro = self.instance.class_ref.mro

        try:
            start_index = mro.index(self.start_class) + 1
        except ValueError:
            return None, RTError(
                name_tok.pos_start,
                name_tok.pos_end,
                "Current class not found in MRO",
                context,
            )

        for i in range(start_index, len(mro)):
            cls = mro[i]
            method = cls.methods.get(method_name)
            if method:
                return method.copy().bind_to_instance(self.instance), None

        return None, RTError(
            name_tok.pos_start,
            name_tok.pos_end,
            f"Method '{method_name}' not found in superclasses",
            context,
        )

    def execute(self, args, interpreter):
        res = RTResult()
        mro = self.instance.class_ref.mro

        try:
            start_index = mro.index(self.start_class) + 1
        except ValueError:
            return res.failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "Current class not found in MRO",
                    self.context,
                )
            )

        method = None
        for i in range(start_index, len(mro)):
            cls = mro[i]
            if cls.name in cls.methods:
                method = cls.methods[cls.name]
                break

        if method:
            return (
                method.copy().bind_to_instance(self.instance).execute(args, interpreter)
            )

        if len(args) > 0:
            return res.failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "No constructor found in superclasses",
                    self.context,
                )
            )

        return res.success(Number.null.copy())

    def copy(self):
        return (
            Super(self.instance, self.start_class)
            .set_context(self.context)
            .set_pos(self.pos_start, self.pos_end)
        )


class Type(Value):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def copy(self):
        return (
            Type(self.name)
            .set_context(self.context)
            .set_pos(self.pos_start, self.pos_end)
        )

    def __repr__(self):
        return f"<type {self.name}>"


class Enum(Value):
    def __init__(self, name, elements_dict):
        super().__init__()
        self.name = name
        self.elements_dict = elements_dict

    def get_attr(self, name_tok, context=None):
        name = name_tok.value
        if name in self.elements_dict:
            val = self.elements_dict[name]
            return val.copy().set_pos(name_tok.pos_start, name_tok.pos_end), None
        return None, RTError(
            name_tok.pos_start,
            name_tok.pos_end,
            f"Enum '{self.name}' has no case '{name}'",
            self.context,
        )

    def set_attr(self, name_tok, value, context=None, visibility=None, as_final=False):
        return None, RTError(
            name_tok.pos_start,
            name_tok.pos_end,
            f"Cannot reassign enum case '{name_tok.value}'",
            self.context,
        )

    def get_comparison_eq(self, other, visited=None):
        if isinstance(other, Enum):
            return Number(1 if self is other else 0).set_context(self.context), None
        return None, self.illegal_operation(other)

    def get_comparison_ne(self, other):
        if isinstance(other, Enum):
            return Number(1 if self is not other else 0).set_context(self.context), None
        return None, self.illegal_operation(other)

    def copy(self):
        copy = Enum(self.name, self.elements_dict)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __repr__(self):
        return f"<enum {self.name}>"


class BoundMethod(BaseFunction):
    def __init__(self, name, function_to_bind, instance):
        super().__init__(name)
        self.function_to_bind = function_to_bind
        self.instance = instance
        self.context = function_to_bind.context
        self.set_pos(function_to_bind.pos_start, function_to_bind.pos_end)

        self.visibility = getattr(function_to_bind, "visibility", "PUBLIC")
        self.defining_class = getattr(function_to_bind, "defining_class", None)
        self.is_static = getattr(function_to_bind, "is_static", False)

    def bind_to_instance(self, instance):
        return BoundMethod(self.name, self.function_to_bind, instance)

    def execute(self, args, interpreter):
        res = RTResult()

        if isinstance(self.function_to_bind, FunctionGroup):
            full_args = [self.instance] + args
            return self.function_to_bind.execute(full_args, interpreter)

        new_context = self.function_to_bind.generate_new_context()

        new_context.active_class = self.function_to_bind.defining_class

        original_arg_names = self.function_to_bind.arg_names

        new_context.symbol_table.set("THIS", self.instance)

        actual_args = args
        if len(args) > 0 and args[0] is self.instance:
            actual_args = args[1:]

        if len(original_arg_names) > 0 and original_arg_names[0] == "THIS":
            expected_arg_names = original_arg_names[1:]
        else:
            expected_arg_names = original_arg_names

        res.register(
            self.function_to_bind.check_and_populate_args(
                expected_arg_names, actual_args, new_context
            )
        )

        if res.error:
            return res

        value_result = interpreter.visit(self.function_to_bind.body_node, new_context)

        if value_result.error:
            return value_result

        if value_result.should_return:
            return res.success(value_result.return_value)

        return res.success(value_result.value or Number.null.copy())

    def copy(self):
        return (
            BoundMethod(self.name, self.function_to_bind.copy(), self.instance)
            .set_context(self.context)
            .set_pos(self.pos_start, self.pos_end)
        )


class BuiltInFunction(BaseFunction):
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

            if text:
                text = text.rstrip("\n")

            return res.success(String(text))

        elif self.name == "STR":
            res.register(self.check_args(["value"], args))
            if res.error:
                return res

            val = args[0]
            if isinstance(val, String):
                return res.success(String(val.value))
            else:
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
                val = int(float(arg.value))
                return res.success(Number(val))
            except ValueError:
                return res.failure(
                    RTError(
                        self.pos_start,
                        self.pos_end,
                        f"Cannot convert '{arg.value}' to INT",
                        self.context,
                    )
                )

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
                return res.success(Number(val))
            except ValueError:
                return res.failure(
                    RTError(
                        self.pos_start,
                        self.pos_end,
                        f"Cannot convert '{arg.value}' to FLOAT",
                        self.context,
                    )
                )

        elif self.name == "BOOL":
            res.register(self.check_args(["value"], args))
            if res.error:
                return res

            is_true = args[0].is_true()
            return res.success(Number.true.copy() if is_true else Number.false.copy())

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
                return res.success(Number(len(str(arg.value))))
            elif isinstance(arg, (Function, BuiltInFunction, Class)):
                return res.success(Number(1))

            return res.success(Number(0))

        return res.failure(
            RTError(
                self.pos_start,
                self.pos_end,
                f"Built-in function '{self.name}' is not defined.",
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


def bind_to_instance(self, instance):
    return BoundMethod(self.name, self, instance)


Function.bind_to_instance = bind_to_instance
