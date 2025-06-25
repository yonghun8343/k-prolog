from typing import Dict, List, Tuple
from PARSER.ast import Struct, Term, Variable


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
    if not xs or not ys:
        return False, {}
    if ys and isinstance(ys[0], Variable):
        y = ys[0].name
        if y in old_unif:
            return match_params([old_unif[y]] + xs[1:], ys[1:], old_unif)
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
            bound_value = old_unif[x]
            success, new_unif = match_params([bound_value], [ys[0]], old_unif)
            if success:
                return match_params(xs[1:], ys[1:], new_unif)
            else:
                return False, {}
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
        merged = substitute_unification(unif, old_unif)
        return match_params(rest_xs, rest_ys, merged)
    return False, {}
