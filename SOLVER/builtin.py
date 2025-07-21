# coding: utf-8
from typing import Dict, List, Tuple

from err import (
    ErrArithmetic,
    ErrDivisionByZero,
    ErrNotNumber,
    ErrParsing,
    ErrProlog,
    ErrSyntax,
    ErrUninstantiated,
    ErrUnknownOperator,
    ErrUnknownPredicate,
    handle_error,
)
from PARSER.ast import Struct, Term, Variable
from PARSER.Data.list import (
    handle_list_append,
    handle_list_length,
    handle_list_permutation,
)
from PARSER.parser import parse_struct
from UTIL.str_util import struct_to_infix

from .unification import extract_variable, match_params, substitute_term


def handle_is(
    goal: Struct, rest_goals: List[Term], old_unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 2:
        raise ErrUnknownPredicate(":=", len(goal.params))

    left, right = goal.params
    try:
        result = evaluate_arithmetic(right, old_unif)

        if isinstance(result, Variable):
            raise ErrUninstantiated(result.name, "산술 표현식")

        result_term = Struct(
            str(int(result) if result.is_integer() else result), 0, []
        )

        success, new_unif = match_params([left], [result_term], old_unif)
        return success, rest_goals, [new_unif] if success else []

    except ErrProlog as e:
        handle_error(e, ":= 내장함수")
        return False, [], []


def evaluate_arithmetic(expr: Term, unif: Dict[str, Term]) -> float:
    expr = substitute_term(unif, expr)

    if isinstance(expr, Variable):
        raise ErrUninstantiated(expr.name, "산술 표현식")
    elif isinstance(expr, Struct):
        if expr.arity == 0:
            try:
                return float(expr.name)
            except ValueError as e:
                raise ErrNotNumber(expr.name) from e
        elif expr.arity == 2:
            left_val = evaluate_arithmetic(expr.params[0], unif)
            right_val = evaluate_arithmetic(expr.params[1], unif)
            if expr.name == "+":
                return left_val + right_val
            elif expr.name == "-":
                return left_val - right_val
            elif expr.name == "*":
                return left_val * right_val
            elif expr.name == "/":
                if right_val == 0:
                    raise ErrDivisionByZero()
                return left_val / right_val
            elif expr.name == "//":
                if right_val == 0:
                    raise ErrDivisionByZero()
                return float(int(left_val // right_val))
            elif expr.name == "나머지":
                if right_val == 0:
                    raise ErrDivisionByZero()
                return left_val % right_val
            else:
                raise ErrUnknownOperator(expr.name)
        elif expr.arity == 1:
            val = evaluate_arithmetic(expr.params[0], unif)
            if expr.name == "-":
                return -val
            elif expr.name == "+":
                return val
            else:
                raise ErrUnknownOperator(expr.name)

        else:
            raise ErrArithmetic(expr.name)

    return None


def handle_comparison(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 2:
        raise ErrUnknownPredicate(goal.name, len(goal.params))

    left, right = goal.params
    try:
        left = evaluate_arithmetic(left, unif)
        right = evaluate_arithmetic(right, unif)

    except ErrProlog as e:
        handle_error(e, "산술 계산")

    if goal.name == ">":
        success = left > right
    elif goal.name == "<":
        success = left < right
    elif goal.name == ">=":
        success = left >= right
    elif goal.name == "=<":
        success = left <= right
    elif goal.name == "=:=":
        success = left == right
    elif goal.name == "=\=":
        success = left != right
    else:
        return False, [], []

    return success, rest_goals, [unif]


def handle_equals(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 2:
        raise ErrUnknownPredicate("=", len(goal.params))

    left, right = goal.params

    success, new_unif = match_params([left], [right], unif)
    return success, rest_goals, [new_unif] if success else []


def handle_write(  # need to take care of string
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 1:
        raise ErrUnknownPredicate("쓰기", len(goal.params))

    writeStr = str(goal.params[0])
    new_unif = extract_variable([writeStr], unif)
    if new_unif:
        print(new_unif.get(writeStr))
        return True, rest_goals, [unif]

    if writeStr.startswith('"') and writeStr.endswith('"'):
        print(writeStr[1:-1])
        return True, rest_goals, [unif]

    if writeStr.startswith('"') or writeStr.endswith('"'):
        raise ErrParsing(f"{writeStr}")

    if writeStr.startswith("'") and writeStr.endswith("'"):
        print(writeStr[1:-1])
        return True, rest_goals, [unif]

    if writeStr.startswith("'") or writeStr.endswith("'"):
        raise ErrParsing({writeStr})

    struct_form = parse_struct(writeStr)
    print(struct_to_infix(struct_form))
    return True, rest_goals, [unif]


def handle_read(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 1:
        raise ErrUnknownPredicate("읽기", len(goal.params))

    var = goal.params[0]

    if not isinstance(var, Variable):
        return False, rest_goals, []

    lines = []
    while True:
        try:
            line = input("|: ")
            lines.append(line)
            if line.strip().endswith("."):
                break
        except EOFError:
            return False, rest_goals, []

    full_input = " ".join(line.strip() for line in lines)
    if full_input.endswith("."):
        full_input = full_input[:-1]

    full_input = full_input.strip()

    if not full_input:
        return False, rest_goals, []

    input_term = Struct(full_input, 0, [])

    success, new_unif = match_params([var], [input_term], unif)

    if success:
        return True, rest_goals, [new_unif]
    else:
        return False, rest_goals, []


def handle_atomic(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 1:
        raise ErrUnknownPredicate("단순", len(goal.params))

    param = goal.params[0]
    if (
        isinstance(param, Variable)
        or param.name[0].isupper()
        or param.name[0] == "_"
        or param.arity != 0
    ):
        return False, [], []

    return True, rest_goals, [unif]


def handle_integer(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 1 or goal.params[0].arity != 0:
        raise ErrUnknownPredicate("정수", len(goal.params))

    try:
        int(goal.params[0].name)
        return True, rest_goals, [unif]
    except ValueError:
        return False, [], []


def handle_nl(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 0:
        raise ErrUnknownPredicate("줄바꿈", len(goal.params))

    print()
    return True, rest_goals, [unif]


def handle_writeln(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 1:
        raise ErrUnknownPredicate("쓰고줄바꿈", len(goal.params))

    success, goals, new_unif = handle_write(goal, rest_goals, unif)
    # print()

    return success, goals, new_unif


def handle_number(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 1:
        raise ErrUnknownPredicate("수", len(goal.params))

    if goal.params[0].name.isnumeric():
        return True, rest_goals, [unif]

    return False, rest_goals, [unif]


BUILTINS = {
    "halt": None,
    "is": handle_is,
    ":=": handle_is,
    ">": handle_comparison,
    "<": handle_comparison,
    ">=": handle_comparison,
    "=<": handle_comparison,
    "=:=": handle_comparison,
    "=\=": handle_comparison,
    "=": handle_equals,
    "append": handle_list_append,
    "접합": handle_list_append,
    "length": handle_list_length,
    "길이": handle_list_length,
    "permutation": handle_list_permutation,
    "순열": handle_list_permutation,
    "write": handle_write,
    "쓰기": handle_write,
    "writeln": handle_writeln,
    "쓰고줄바꿈": handle_writeln,
    "read": handle_read,
    "읽기": handle_read,
    "atomic": handle_atomic,
    "단순": handle_atomic,
    "integer": handle_integer,
    "정수": handle_integer,
    "nl": handle_nl,
    "줄바꿈": handle_nl,
    "number": handle_number,
    "수": handle_number,
}


def has_builtin(builtin: str) -> bool:
    return builtin in BUILTINS


def handle_builtins(
    goal: Struct, rest_goals: List[Term], old_unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if goal.name == "halt" or goal.name == "종료":
        if goal.arity == 0:
            import sys

            sys.exit(0)
        else:
            raise ErrUnknownPredicate("종료", goal.arity)
    if goal.name not in BUILTINS:
        return False, [], []
    return BUILTINS[goal.name](goal, rest_goals, old_unif)
