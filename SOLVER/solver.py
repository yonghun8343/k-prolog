from typing import Dict, List, Tuple

from PARSER.ast import Struct, Term, Variable

from .builtin import handle_builtins, has_builtin
from .unification import (
    extract_variable,
    match_params,
    substitute_term,
)


def get_variables(terms: List[Term]) -> List[str]:
    result = []
    for t in terms:
        if isinstance(t, Variable):
            result.append(t.name)
        elif isinstance(t, Struct):
            result.extend(get_variables(t.params))
    return result


def is_relevant(goal: Term, clause: List[Term]) -> bool:
    if not clause or not isinstance(goal, Struct):
        return False
    head = clause[0]
    return (
        isinstance(head, Struct)
        and head.name == goal.name
        and head.arity == goal.arity
    )


def match_predicate(
    goal: Struct,
    rest_goals: List[Term],
    old_unif: Dict[str, Term],
    clause: List[Term],
) -> Tuple[bool, List[Term], Dict[str, Term]]:
    head, *conds = clause
    if not isinstance(head, Struct):
        return False, [], {}
    ok, unif = match_params(goal.params, head.params, old_unif)
    if ok:
        substituted_goals = [substitute_term(unif, p) for p in conds]
        new_goals = substituted_goals + rest_goals
        return True, new_goals, unif
    return False, [], {}


# rename all variables in a clause to avoid conflicts
def init_rules(clause: List[Term], counter: int) -> Tuple[List[Term], int]:
    vars_in_clause = get_variables(clause)
    var_map = {}
    current_counter = counter

    for var_name in vars_in_clause:
        if var_name not in var_map:
            var_map[var_name] = Variable(f"TEMP{current_counter}")
            current_counter += 1

    renamed_clause = [substitute_term(var_map, term) for term in clause]
    return renamed_clause, current_counter


def solve_with_unification(
    program: List[List[Term]],
    goals: List[Term],
    old_unif: Dict[str, Term],
    seq: int,
) -> Tuple[bool, List[Dict[str, Term]], int]:
    if not goals:
        return True, [old_unif], seq
    x, *rest = goals

    if isinstance(x, Struct) and has_builtin(x.name):
        success, new_unif = handle_builtins(x, old_unif)
        if success:
            return solve_with_unification(program, rest, new_unif, seq)

    clauses = [c for c in program if is_relevant(x, c)]

    all_solutions = []
    for clause in clauses:
        renamed_clause, new_seq = init_rules(clause, seq)
        seq = new_seq
        is_match, new_goals, unif = match_predicate(
            x, rest, old_unif, renamed_clause
        )
        if is_match:
            success, solutions, final_seq = solve_with_unification(
                program, new_goals, unif, seq
            )
            seq = final_seq
            if success:
                all_solutions.extend(solutions)
    return bool(all_solutions), all_solutions, seq


def solve(
    program: List[List[Term]], goals: List[Term]
) -> Tuple[bool, List[Dict[str, Term]]]:
    result, unifs, _ = solve_with_unification(program, goals, {}, 0)
    final_unifs =  [extract_variable(get_variables(goals), u) for u in unifs]
    return result, [extract_variable(get_variables(goals), u) for u in unifs]
