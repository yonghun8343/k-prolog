from typing import Dict, List, Tuple

from PARSER.ast import Struct, Term, Variable
from PARSER.Data.list import handle_list_append, handle_list_length, handle_list_permutation
from .unification import match_params, substitute_term
from err import *


# TODO should builtins be a class?
def handle_is(
    goal: Struct, rest_goals: List[Term], old_unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 2:
        return False, [], []

    left, right = goal.params
    try:
        result = evaluate_arithmetic(right, old_unif)

        if isinstance(result, Variable):
            raise ErrUninstantiated(result.name, "Arithmetic Expression")

        result_term = Struct(
            str(int(result) if result.is_integer() else result), 0, []
        )

        success, new_unif = match_params([left], [result_term], old_unif)
        return success, rest_goals, [new_unif] if success else []

    except ErrProlog as e:
        handle_error(e, "is predicate")
        return False, [], []


def evaluate_arithmetic(expr: Term, unif: Dict[str, Term]) -> float:
    expr = substitute_term(unif, expr)

    if isinstance(expr, Variable):
        raise ErrUninstantiated(expr.name, "Arithmetic Expression")
    elif isinstance(expr, Struct):
        if expr.arity == 0:
            try:
                return float(expr.name)
            except ValueError:
                raise ErrNotNumber(expr.name)
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
            elif expr.name == "mod":
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
        return False, [], []
    left, right = goal.params
    try:
        left = evaluate_arithmetic(left, unif)
        right = evaluate_arithmetic(right, unif)

    except ErrProlog as e:
        handle_error(e, "arithmetic evaluation")

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
        return False, [], []
    left, right = goal.params

    success, new_unif = match_params([left], [right], unif)
    return success, rest_goals, [new_unif] if success else []


BUILTINS = {
    "is": handle_is,
    ">": handle_comparison,
    "<": handle_comparison,
    ">=": handle_comparison,
    "=<": handle_comparison,
    "=:=": handle_comparison,
    "=\=": handle_comparison,
    "=": handle_equals,
    "append": handle_list_append,
    "length": handle_list_length,
    "permutation": handle_list_permutation,
    
}


def has_builtin(builtin: str) -> bool:
    return builtin in BUILTINS


def handle_builtins(
    goal: Struct, rest_goals: List[Term], old_unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if goal.name not in BUILTINS:
        return False, [], []
    return BUILTINS[goal.name](goal, rest_goals, old_unif)
