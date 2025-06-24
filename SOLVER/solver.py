from typing import Dict, List, Tuple

from PARSER.ast import Struct, Term, Variable

from .builtin import handle_builtins, has_builtin
from .unification import (
    extract_variable,
    get_variables,
    match_params,
    substitute_term,
)


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
        new_goals = [substitute_term(unif, p) for p in conds + rest_goals]
        return True, new_goals, unif
    return False, [], {}


# def init_rules(
#     clauses: List[List[Term]], seq: int
# ) -> Tuple[List[List[Term]], int]:
#     if not clauses:
#         return [], seq
#     first, *rest = clauses
#     y, new_seq = init_rule(first, seq)
#     ys, final_seq = init_rules(rest, new_seq)
#     return [y] + ys, final_seq

# def init_rules(clauses: List[List[Term]], seq: int) -> Tuple[List[List[Term]], int]:
#     if not clauses:
#         return [], seq
#     rules = []
#     for clause in clauses:
#         y, new_seq = init_rule(clause, seq)
#         seq = new_seq
#         rules += y
#     return rules, seq


# def init_rule(terms: List[Term], seq: int) -> Tuple[List[Term], int]:
#     vars = get_variables(terms)
#     replacement, new_seq = get_replacement(vars, seq, {})
#     new_terms = [substitute_term(replacement, t) for t in terms]
#     return new_terms, new_seq

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

# maps original variable names to new temporary ones to avoid conflicts
# def get_replacement(
#     vars: List[str],
#     seq: int,
#     replacement: Dict[str, Term],
# ) -> Tuple[Dict[str, Term], int]:
#     if not vars:
#         return replacement, seq
#     x, *xs = vars
#     temp = Variable(f"TEMP{seq}")
#     repl2 = replacement.copy()
#     repl2[x] = temp
#     return get_replacement(xs, seq + 1, repl2)


def solve_with_unification(  # recursively solves down to the non-goal level
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
        is_match, new_goals, unif = match_predicate(x, rest, old_unif, clause)
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
    return result, [extract_variable(get_variables(goals), u) for u in unifs]
