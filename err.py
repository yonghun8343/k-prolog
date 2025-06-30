import sys
from typing import Optional, Any

IsVerbose = False


def eprint(*args, **kwargs) -> None:
    print(*args, file=sys.stderr, **kwargs)


def handle_error(error: Exception, context: str = "") -> None:
    if IsVerbose:
        eprint(f"Context: {context}")
        eprint(f"Error type: {type(error).__name__}")
    eprint(f"Error: {error}")


class ErrProlog(Exception):
    pass


class ErrSyntax(ErrProlog):
    def __init__(
        self,
        message: str = "",
        line: Optional[int] = None,
        pos: Optional[int] = None,
    ):
        self.message = message
        self.line = line
        self.pos = pos

    def __str__(self) -> str:
        base = "Syntax error"
        if self.line is not None:
            base += f" (line {self.line}"
            if self.pos is not None:
                base += f", position {self.pos}"
            base += ")"
        if self.message:
            base += f": {self.message}"
        return base


class ErrParenthesis(ErrSyntax):
    def __init__(self, missing_type: str = "closing"):
        self.missing_type = missing_type

    def __str__(self) -> str:
        if self.missing_type == "closing":
            return "Syntax error: missing closing parenthesis"
        else:
            return "Syntax error: missing opening parenthesis"


class ErrInvalidTerm(ErrSyntax):
    def __init__(self, term: str):
        self.term = term

    def __str__(self) -> str:
        return f"Syntax error: invalid term '{self.term}'"


class ErrExecution(ErrProlog):
    pass


class ErrUninstantiated(ErrExecution):
    def __init__(self, variable: str = "", context: str = ""):
        self.variable = variable
        self.context = context

    def __str__(self) -> str:
        base = "ERROR: Arguments are not sufficiently instantiated"
        if self.variable:
            base += f" (variable: {self.variable})"
        if self.context:
            base += f" in {self.context}"
        return base


class ErrArithmetic(ErrExecution):
    def __init__(self, operation: str, reason: str = ""):
        self.operation = operation
        self.reason = reason

    def __str__(self) -> str:
        base = f"Arithmetic error: {self.operation}"
        if self.reason:
            base += f" - {self.reason}"
        return base


class ErrDivisionByZero(ErrArithmetic):
    def __init__(self):
        super().__init__("Division by zero")


class ErrNotNumber(ErrArithmetic):
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return f"Arithmetic error: '{self.value}' is not a number"


class ErrUnknownOperator(ErrArithmetic):
    def __init__(self, operator: str):
        self.operator = operator

    def __str__(self) -> str:
        return f"Arithmetic error: unknown operator '{self.operator}'"


class ErrDatabase(ErrProlog):
    pass


class ErrUnknownPredicate(ErrDatabase):
    def __init__(self, predicate: str, arity: int):
        self.predicate = predicate
        self.arity = arity

    def __str__(self) -> str:
        return f"ERROR: Unknown procedure '{self.predicate}/{self.arity}'"


class ErrFileNotFound(ErrDatabase):
    def __init__(self, filename: str):
        self.filename = filename

    def __str__(self) -> str:
        return f"ERROR: File not found '{self.filename}'"


class ErrInvalidClause(ErrDatabase):
    def __init__(self, clause: str, reason: str = ""):
        self.clause = clause
        self.reason = reason

    def __str__(self) -> str:
        base = f"ERROR: Invalid clause '{self.clause}'"
        if self.reason:
            base += f" - {self.reason}"
        return base


class ErrUnification(ErrExecution):
    def __init__(self, term1: str, term2: str, reason: str = ""):
        self.term1 = term1
        self.term2 = term2
        self.reason = reason

    def __str__(self) -> str:
        base = f"Unification error: cannot unify '{self.term1}' with '{self.term2}'"
        if self.reason:
            base += f" - {self.reason}"
        return base


class ErrOccursCheck(ErrUnification):
    def __init__(self, variable: str, term: str):
        self.variable = variable
        self.term = term

    def __str__(self) -> str:
        return f"Occurs check error: variable '{self.variable}' occurs in term '{self.term}'"


class ErrREPL(ErrProlog):
    pass


class ErrInvalidCommand(ErrREPL):
    def __init__(self, command: str):
        self.command = command

    def __str__(self) -> str:
        return f"ERROR: Invalid command '{self.command}'"


class ErrCommandFormat(ErrREPL):
    def __init__(self, command: str, expected_format: str):
        self.command = command
        self.expected_format = expected_format

    def __str__(self) -> str:
        return f"ERROR: Command format error. '{self.command}' (expected format: {self.expected_format})"
