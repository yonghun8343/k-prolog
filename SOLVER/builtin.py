from typing import Dict, List, Tuple

from PARSER.ast import Struct, Term, Variable

from .unification import match_params, substitute_term

#TODO should builtins be a class?
def handle_is(
    goal: Struct, old_unif: Dict[str, Term]
) -> Tuple[bool, List[Term], Dict[str, Term]]:
    if len(goal.params) != 2:
        return False, [], {}

    left, right = goal.params
    try:

        result = evaluate_arithmetic(right, old_unif)

        result_term = Struct(str(int(result) if result.is_integer() else result), 0, [])

        if isinstance(right_substituted, Variable):
            raise ValueError("Arguments are not sufficiently instantiated.")

        success, new_unif = match_params([left], [result_term], old_unif)
        return success, new_unif if success else {}

    except ValueError as e:
        print(f"ERROR: {e}")
        return False, [], {}

def evaluate_arithmetic(expr: Term, unif: Dict[str, Term]) -> float:
    expr = substitute_term(unif, expr)

    if isinstance(expr, Variable):
        raise ValueError(f"Arguments are not sufficiently instantiated: {expr}")
    elif isinstance(expr, Struct):
        if expr.arity == 0:
            try:
                return float(expr.name) # what
            except ValueError:
                raise ValueError(f"Not a number: {expr.name}")
        elif expr.arity == 2:
            left_val = evaluate_arithmetic(expr.params[0], unif)
            right_val  = evaluate_arithmetic(expr.params[1], unif)
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
        return False, [], {}
    left, right = goal.params
    try:
        left = evaluate_arithmetic(left, unif)
        right = evaluate_arithmetic(right, unif)

        # left_result = Struct(str(int(left) if left.is_integer() else left), 0, [])
        # right_result = Struct(str(int(right) if right.is_integer() else right), 0, [])

        
        # if isinstance(left_result, Variable) or isinstance(right_result, Variable):
        #     raise ValueError("Arguments are not sufficiently instantiated.")
        if goal.name == ">":
        elif goal.name == "<":
        elif g
        success, new_unif = match_params([left], [right_result])
    except ValueError as e:
        raise ValueError(f"Arithmetic: {e}")
        return False, [], {}


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
    
