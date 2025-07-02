from PARSER.ast import Term, Variable, Struct
from SOLVER.unification import substitute_term, match_params
from err import *

from typing import List, Union, Dict, Tuple
import itertools


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
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 3 or goal.arity != 3:
        return False, [], []

    l1, l2, l3 = goal.params
    l1 = substitute_term(unif, l1)
    l2 = substitute_term(unif, l2)
    l3 = substitute_term(unif, l3)

    if is_empty_list(l1):
        success, new_unif = match_params([l2], [l3], unif)
        return success, rest_goals, [new_unif] if success else []

    if is_list_cons(l1):
        head1, tail1 = get_head_tail(l1)

        if isinstance(l3, Variable):
            new_var = Variable(f"_R{id(goal)}")
            new_l3 = Struct(".", 2, [head1, new_var])

            success, unif1 = match_params([l3], [new_l3], unif)
            if success:
                recursive_goal = Struct("append", 3, [tail1, l2, new_var])
                return True, [recursive_goal] + rest_goals, [unif1]

        elif is_list_cons(l3):
            head3, tail3 = get_head_tail(l3)
            success, unif3 = match_params([head1], [head3], unif)
            if success:
                recursive_goal = Struct("append", 3, [tail1, l2, tail3])
                return True, [recursive_goal] + rest_goals, [unif3]
    return False, [], []


def handle_list_length(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 2 or goal.arity != 2:
        return False, [], {}

    list_term, length_term = goal.params
    list_term = substitute_term(unif, list_term)
    length_term = substitute_term(unif, length_term)

    # length(List, N) where List is instantiated and N is variable
    if not isinstance(list_term, Variable):
        actual_length = count_list_length(list_term)
        if actual_length is not None:
            length_struct = Struct(str(actual_length), 0, [])
            success, new_unif = match_params(
                [length_term], [length_struct], unif
            )
            return success, rest_goals, [new_unif] if success else []

    # # length(List, N) where N is instantiated and List is variable
    elif isinstance(list_term, Variable) and not isinstance(
        length_term, Variable
    ):
        if isinstance(length_term, Struct) and length_term.arity == 0:
            try:
                n = int(length_term.name)
                if n >= 0:
                    generated_list = generate_list(n)
                    success, new_unif = match_params(
                        [list_term], [generated_list], unif
                    )
                    return success, rest_goals, [new_unif] if success else []
            except ValueError:
                raise ErrList("Error generating list")
    elif isinstance(list_term, Variable) and isinstance(length_term, Variable):
        raise ErrUninstantiated(f"{list_term}, {length_term}", "list length")

    return False, [], []


def count_list_length(list_term: Term) -> int:
    count = 0

    while True:
        if isinstance(list_term, Struct):
            if list_term.name == "[]":
                return count
            elif list_term.name == ".":
                count += 1
                list_term = list_term.params[1]
            else:
                return None
        else:
            return None


def handle_list_permutation(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 2 or goal.arity != 2:
        return False, [], {}

    list1, list2 = goal.params

    list1 = substitute_term(unif, list1)
    list2 = substitute_term(unif, list2)

    if is_empty_list(list1) and is_empty_list(list2):
        return True, rest_goals, [unif]

    if is_empty_list(list1) or is_empty_list(list2):
        return False, [], []

    # TODO think about if this(checking if isinstance) needs to be more complex
    if (not isinstance(list1, Variable)) and (not isinstance(list2, Variable)):
        list1_extr = extract_list(list1)
        list2_extr = extract_list(list2)

        if list1_extr is not None and list2_extr is not None:
            permutations = list(itertools.permutations(list1_extr))
            for permutation in permutations:
                if list2_extr == list(permutation):
                    return True, rest_goals, [unif]
        return False, [], []

    if isinstance(list2, Variable):
        list1_extr = extract_list(list1)
        all_solutions = []
        for permutation in itertools.permutations(list1_extr):
            perm_struct = PrologList(permutation).to_struct()
            success, new_unif = match_params([list2], [perm_struct], unif)
            if success:
                all_solutions.append(new_unif)

        return len(all_solutions) > 0, rest_goals, all_solutions
    if isinstance(list1, Variable):
        list2_extr = extract_list(list2)
        all_solutions = []
        for permutation in itertools.permutations(list2_extr):
            perm_struct = PrologList(permutation).to_struct()
            success, new_unif = match_params([list1], [perm_struct], unif)
            if success:
                all_solutions.append(new_unif)

        return len(all_solutions) > 0, rest_goals, all_solutions
        
    return False, [], []


def extract_list(term: Term) -> List:
    res = []
    while True:
        if isinstance(term, Struct):
            if term.name == "[]":
                return res
            elif term.name == ".":
                left, term = term.params
                if not isinstance(left, Variable):
                    res.append(left.name)
                else:
                    return None
        else:
            return None


# def handle_list_select(
#     goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
# ) -> Tuple[bool, List[Term], Dict[str, Term]]:
#     if len(goal.params) != 3 or goal.arity != 3:
#         return False, rest_goals, {}

#     elt, list_term, remainder = goal.params
#     elt = substitute_term(unif, elt)
#     list_term = substitute_term(unif, list_term)
#     remainder = substitute_term(unif, remainder)


def generate_list(n: int) -> Term:
    if n == 0:
        return Struct("[]", 0, [])

    result = Struct("[]", 0, [])
    for i in range(n):
        var = Variable(f"_")
        result = Struct(".", 2, [var, result])

    return result


def is_empty_list(term: Term) -> bool:
    return isinstance(term, Struct) and term.name == "[]" and term.arity == 0


def is_list_cons(term: Term) -> bool:
    return isinstance(term, Struct) and term.name == "." and term.arity == 2


def get_head_tail(term: Term) -> Tuple[Term, Term]:
    if is_list_cons(term):
        return term.params[0], term.params[1]
    raise ErrList("Not a list cons structure")
