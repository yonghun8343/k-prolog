from PARSER.ast import Term, Variable, Struct
from SOLVER.unification import substitute_term, match_params
from typing import List, Union, Dict, Tuple
from err import *


class PrologList(Term):
    def __init__(self, elements: List[Term] = None, tail: Term = None):
        self.elements = elements or []
        self.tail = tail

    def to_struct(self) -> Term:
        if not self.elements:
            if self.tail is None:
                return Struct("[]", 0, [])
            else:
                return self.tail

        result = self.tail if self.tail else Struct("[]", 0, [])

        for element in reversed(self.elements):
            result = Struct(".", 2, [element, result])

        return result

    def __str__(self):
        if not self.elements and self.tail is None:
            return "[]"

        result = "[" + ", ".join(str(e) for e in self.elements)
        if self.tail and not (
            isinstance(self.tail, Struct) and self.tail.name == "[]"
        ):
            result += "|" + str(self.tail)
        result += "]"
        return result


def handle_list_append(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], Dict[str, Term]]:
    if len(goal.params) != 3 or goal.arity != 3:
        return False, [], unif

    l1, l2, l3 = goal.params
    l1 = substitute_term(unif, l1)
    l2 = substitute_term(unif, l2)
    l3 = substitute_term(unif, l3)

    if is_empty_list(l1):
        success, new_unif = match_params([l2], [l3], unif)
        return success, rest_goals, new_unif if success else {}

    if is_list_cons(l1):
        head1, tail1 = get_head_tail(l1)

        if isinstance(l3, Variable):
            new_var = Variable(f"_R{id(goal)}")  # generate unique variable
            new_l3 = Struct(".", 2, [head1, new_var])

            success, unif1 = match_params([l3], [new_l3], unif)
            if success:
                recursive_goal = Struct("append", 3, [tail1, l2, new_var])
                return True, [recursive_goal] + rest_goals, unif1

        elif is_list_cons(l3):
            head3, tail3 = get_head_tail(l3)
            success, unif1 = match_params([head1], [head3], unif)
            if success:
                recursive_goal = Struct("append", 3, [tail1, l2, tail3])
                return True, [recursive_goal] + rest_goals, unif1
    return False, [], {}


def handle_list_length(
    goal: Struct, unif: Dict[str, Term]
) -> Tuple[bool, Dict[str, Term]]:
    if len(goal.params) != 2 or goal.arity != 2:
        return False, {}


def is_empty_list(term: Term) -> bool:
    return isinstance(term, Struct) and term.name == "[]" and term.arity == 0


def is_list_cons(term: Term) -> bool:
    return isinstance(term, Struct) and term.name == "." and term.arity == 2


def get_head_tail(term: Term) -> Tuple[Term, Term]:
    if is_list_cons(term):
        return term.params[0], term.params[1]
    raise ErrList("Not a list cons structure")
