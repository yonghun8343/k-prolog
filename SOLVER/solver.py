from typing import Dict, List, Tuple

from PARSER.ast import Struct, Term, Variable


def get_variables(terms: List[Term]) -> List[str]:
    result = []
    for t in terms:
        if isinstance(t, Variable):
            result.append(t.name)
        elif isinstance(t, Struct):
            result.extend(get_variables(t.params))
    return result


def extract_variable(vars: List[str], unif: Dict[str, Term]) -> Dict[str, Term]:
    return {v: unif[v] for v in vars if v in unif}


def substitute_term(unification: Dict[str, Term], term: Term) -> Term:
    if isinstance(term, Variable):
        return unification.get(term.name, term)
    elif isinstance(term, Struct):
        return Struct(
            term.name,
            term.arity,
            [substitute_term(unification, p) for p in term.params],
        )
    return term


def substitute(unification: Dict[str, Term], terms: List[Term]) -> List[Term]:
    return [substitute_term(unification, t) for t in terms]


def substitute_unification(
    sub: Dict[str, Term], unification: Dict[str, Term]
) -> Dict[str, Term]:
    return {k: substitute_term(sub, v) for k, v in unification.items()}


def is_relevant(goal: Term, clause: List[Term]) -> bool:
    if not clause or not isinstance(goal, Struct):
        return False
    head = clause[0]
    return (
        isinstance(head, Struct) and head.name == goal.name and head.arity == goal.arity
    )


def match_structs(
    a: Struct, b: Struct, old_unif: Dict[str, Term]
) -> Tuple[bool, Dict[str, Term]]:
    if a.name == b.name and a.arity == b.arity:
        return match_params(a.params, b.params, old_unif)
    return False, {}


def match_params(
    xs: List[Term], ys: List[Term], old_unif: Dict[str, Term]
) -> Tuple[bool, Dict[str, Term]]:
    if not xs and not ys:
        return True, old_unif
    if ys and isinstance(ys[0], Variable):
        y = ys[0].name
        sub = {y: xs[0]}
        new_xs = substitute(sub, xs[1:])
        new_ys = substitute(sub, ys[1:])
        new_unif = substitute_unification(sub, old_unif)
        new_unif[y] = xs[0]
        return match_params(new_xs, new_ys, new_unif)
    if xs and isinstance(xs[0], Variable):
        x = xs[0].name
        sub = {x: ys[0]}
        new_xs = substitute(sub, xs[1:])
        new_ys = substitute(sub, ys[1:])
        new_unif = substitute_unification(sub, old_unif)
        new_unif[x] = ys[0]
        return match_params(new_xs, new_ys, new_unif)
    ok, unif = match_structs(xs[0], ys[0], old_unif)
    if ok:
        rest_xs = substitute(unif, xs[1:])
        rest_ys = substitute(unif, ys[1:])
        merged = substitute_unification(unif, old_unif)
        return match_params(rest_xs, rest_ys, merged)
    return False, {}


def match_predicate(
    goal: Struct, rest_goals: List[Term], old_unif: Dict[str, Term], clause: List[Term]
) -> Tuple[bool, List[Term], Dict[str, Term]]:
    head, *conds = clause
    if not isinstance(head, Struct):
        return False, [], {}
    ok, unif = match_params(goal.params, head.params, old_unif)
    if ok:
        new_goals = [substitute_term(unif, p) for p in conds + rest_goals]
        return True, new_goals, unif
    return False, [], {}


def combine_solution(
    triples: List[Tuple[bool, List[Dict[str, Term]], int]],
) -> Tuple[bool, List[Dict[str, Term]], int]:
    if not triples:
        return False, [], -1
    if len(triples) == 1:
        return triples[0]
    first, *rest = triples
    r1, u1, s1 = combine_solution(rest)
    result = first[0] or r1
    unifs = first[1] + u1
    seq = max(first[2], s1)
    return result, unifs, seq


def init_rules(clauses: List[List[Term]], seq: int) -> Tuple[List[List[Term]], int]:
    if not clauses:
        return [], seq
    first, *rest = clauses
    y, new_seq = init_rule(first, seq)
    ys, final_seq = init_rules(rest, new_seq)
    return [y] + ys, final_seq


def init_rule(terms: List[Term], seq: int) -> Tuple[List[Term], int]:
    vars = get_variables(terms)
    replacement, new_seq = get_replacement(vars, seq, {})
    new_terms = [substitute_term(replacement, t) for t in terms]
    return new_terms, new_seq


def get_replacement(
    vars: List[str], seq: int, replacement: Dict[str, Term]
) -> Tuple[Dict[str, Term], int]:
    if not vars:
        return replacement, seq
    x, *xs = vars
    temp = Variable(f"TEMP{seq}")
    repl2 = replacement.copy()
    repl2[x] = temp
    return get_replacement(xs, seq + 1, repl2)


def solve_with_unification(
    program: List[List[Term]], goals: List[Term], old_unif: Dict[str, Term], seq: int
) -> Tuple[bool, List[Dict[str, Term]], int]:
    if not goals:
        return True, [old_unif], seq
    x, *rest = goals
    clauses = [c for c in program if is_relevant(x, c)]
    ps, new_seq = init_rules(clauses, seq)
    triples = []
    for cl in ps:
        is_match, new_goals, unif = match_predicate(x, rest, old_unif, cl)
        if is_match:
            triples.append(solve_with_unification(program, new_goals, unif, new_seq))
    if not triples:
        return False, [], new_seq
    return combine_solution(triples)


def solve(
    program: List[List[Term]], goals: List[Term]
) -> Tuple[bool, List[Dict[str, Term]]]:
    result, unifs, _ = solve_with_unification(program, goals, {}, 0)
    return result, [extract_variable(get_variables(goals), u) for u in unifs]
