from typing import Dict, List, Tuple

from PARSER.ast import Struct, Term, Variable
from err import ErrUnification


def extract_variable(vars: List[str], unif: Dict[str, Term]) -> Dict[str, Term]:
    result = {}
    for v in vars:
        if v in unif and not v.startswith("_G"):
            # fully substitute the value to resolve any remaining temporary variables
            result[v] = substitute_term(unif, unif[v])
    return result


def substitute_term(
    unification: Dict[str, Term],
    term: Term,
    visited: set = None,
    depth: int = 0,
) -> Term:
    # prevent infinite recursion
    if depth > 100:
        return term

    if visited is None:
        visited = set()

    if isinstance(term, Variable):
        if term.name in visited:
            return term  # return original variable to break cycle

        if term.name in unification:
            visited.add(term.name)
            result = substitute_term(
                unification, unification[term.name], visited, depth + 1
            )
            visited.remove(term.name)
            return result
        else:
            return term
    elif isinstance(term, Struct):
        new_params = [
            substitute_term(unification, p, visited, depth + 1)
            for p in term.params
        ]
        result = Struct(term.name, term.arity, new_params)
        return result
    else:
        return term


def substitute(unification: Dict[str, Term], terms: List[Term]) -> List[Term]:
    return [substitute_term(unification, t) for t in terms]


def substitute_unification(
    sub: Dict[str, Term], unification: Dict[str, Term]
) -> Dict[str, Term]:
    return {k: substitute_term(sub, v) for k, v in unification.items()}


def match_structs(
    a: Struct, b: Struct, old_unif: Dict[str, Term]
) -> Tuple[bool, Dict[str, Term]]:
    try:
        if a.name == b.name and a.arity == b.arity:
            success, result_unif = match_params(a.params, b.params, old_unif)
            return success, result_unif
    except Exception as e:
        raise ErrUnification(a, b, "match_structs") from e
    return False, {}


def match_params(
    xs: List[Term], ys: List[Term], old_unif: Dict[str, Term]
) -> Tuple[bool, Dict[str, Term]]:
    if not xs and not ys:
        return True, old_unif
    if not xs or not ys:
        return False, {}
    if ys and isinstance(ys[0], Variable):
        y = ys[0].name
        if y.startswith("_G"):
            return match_params(xs[1:], ys[1:], old_unif)
        elif y in old_unif:
            bound_value = substitute_term(old_unif, ys[0])
            return match_params(xs, [bound_value] + ys[1:], old_unif)
        else:
            sub = {y: xs[0]}
            new_xs = substitute(sub, xs[1:])
            new_ys = substitute(sub, ys[1:])
            new_unif = substitute_unification(sub, old_unif)
            new_unif[y] = xs[0]
            return match_params(new_xs, new_ys, new_unif)
    if xs and isinstance(xs[0], Variable):
        x = xs[0].name
        if x in old_unif:
            substituted_value = substitute_term(old_unif, xs[0])
            return match_params([substituted_value] + xs[1:], ys, old_unif)
        else:
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

        merged = old_unif.copy()
        for key, value in unif.items():
            merged[key] = substitute_term(old_unif, value)
        return match_params(rest_xs, rest_ys, merged)
    return False, {}
