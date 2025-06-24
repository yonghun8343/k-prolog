from typing import Dict, List, Tuple

from PARSER.ast import Struct, Term, Variable

from .unification import match_params, substitute_term


# TODO should builtins be a class?
def handle_is(
    goal: Struct, old_unif: Dict[str, Term]
) -> Tuple[bool, List[Term], Dict[str, Term]]:
    if len(goal.params) != 2:
        return False, [], {}

    left, right = goal.params
    try:
        result = evaluate_arithmetic(right, old_unif)

        if isinstance(result, Variable):
            raise ValueError("Arguments are not sufficiently instantiated.")

        result_term = Struct(
            str(int(result) if result.is_integer() else result), 0, []
        )

        success, new_unif = match_params([left], [result_term], old_unif)
        return success, new_unif if success else {}

    except ValueError as e:
        print(f"ERROR: {e}")
        return False, {}


def evaluate_arithmetic(expr: Term, unif: Dict[str, Term]) -> float:
    expr = substitute_term(unif, expr)

    if isinstance(expr, Variable):
        raise ValueError(f"Arguments are not sufficiently instantiated: {expr}")
    elif isinstance(expr, Struct):
        if expr.arity == 0:
            try:
                return float(expr.name)
            except ValueError:
                raise ValueError(f"Not a number: {expr.name}")
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
                    raise ValueError("Division by zero")
                return left_val / right_val
            elif expr.name == "//":
                if right_val == 0:
                    raise ValueError("Division by zero")
                return float(int(left_val // right_val))
            elif expr.name == "mod":
                if right_val == 0:
                    raise ValueError("Division by zero")
                return left_val % right_val
            else:
                raise ValueError(f"Unknown arithmetic operator: {expr.name}")
        elif expr.arity == 1:
            val = evaluate_arithmetic(expr.params[0], unif)
            if expr.name == "-":
                return -val
            elif expr.name == "+":
                return val
            else:
                raise ValueError(f"Unknown unary operator: {expr.name}")

        else:
            raise ValueError(f"Cannot evaluate: {expr.name}/{expr.arity}")

    return None


def handle_comparison(
    goal: Struct, unif: Dict[str, Term]
) -> Tuple[bool, List[Term], Dict[str, Term]]:
    if len(goal.params) != 2:
        return False, {}
    left, right = goal.params
    try:
        left = evaluate_arithmetic(left, unif)
        right = evaluate_arithmetic(right, unif)

    except ValueError as e:
        raise ValueError(f"Arithmetic: {e}")

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
        return False, {}

    return success, unif


BUILTINS = {
    "is": handle_is,
    ">": handle_comparison,
    "<": handle_comparison,
    ">=": handle_comparison,
    "=<": handle_comparison,
    "=:=": handle_comparison,
    "=\=": handle_comparison,
}


def has_builtin(builtin: str) -> bool:
    return builtin in BUILTINS


def handle_builtins(
    goal: Struct, old_unif: Dict[str, Term]
) -> Tuple[bool, Dict[str, Term]]:
    if goal.name not in BUILTINS:
        return False, old_unif
    return BUILTINS[goal.name](goal, old_unif)
