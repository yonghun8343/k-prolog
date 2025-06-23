from typing import Dict, List, Tuple

from PARSER.ast import Struct, Term, Variable

from .unification import match_params, substitute_term


def handle_is(
    goal: Struct, rest_goals: List[Term], old_unif: Dict[str, Term]
) -> Tuple[bool, List[Term], Dict[str, Term]]:
    if len(goal.params) != 2:
        return False, [], old_unif

    left, right = goal.params

    right_substituted = substitute_term(old_unif, right)

    # call arithmetic operation

    if isinstance(right_substituted, Variable):
        raise ValueError("Arguments are not sufficiently instantiated.")

    success, new_unif = match_params([left], [right], old_unif)

    return success, rest_goals, new_unif if success else old_unif


def handle_comparison_operators(
    goal: Struct, rest_goals: List[Term], old_unif: Dict[str, Term]
) -> Tuple[bool, List[Term], Dict[str, Term]]:
    return None


def handle_arithmetic_operators(
    goal: Struct, rest_goals: List[Term], old_unif: Dict[str, Term]
) -> Tuple[bool, List[Term], Dict[str, Term]]:
    return None


BUILTINS = {
    "is": handle_is,
}


def handle_builtins(
    goal: Struct, rest_goals: List[Term], old_unif: Dict[str, Term]
) -> Tuple[bool, List[Term], Dict[str, Term]]:
    if goal.name in BUILTINS:
        return BUILTINS[goal.name](goal, rest_goals, old_unif)
    return False, [], old_unif
