import itertools
from typing import Dict, List, Tuple

from err import (
    ErrInfiniteGeneration,
    ErrList,
    ErrType,
    ErrUninstantiated,
    ErrUnknownPredicate,
)
from PARSER.ast import Struct, Term, Variable
from SOLVER.unification import match_params, substitute_term


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

    # length(List, N) where N is instantiated and List is variable
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
            except ValueError as e:
                raise ErrList() from e
    elif isinstance(list_term, Variable) and isinstance(length_term, Variable):
        raise ErrUninstantiated(f"{list_term}, {length_term}", "기리")

    return False, [], []


def count_list_length(list_term: Term) -> int:
    count = 0
    if not isinstance(list_term, Term):
        raise ErrList()

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
                    res.append(left)
                else:
                    return None
        else:
            return None


def handle_is_list(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 1 or goal.arity != 1:
        return False, [], {}
    list = goal.params[0]
    is_list = is_list_cons(list) or is_empty_list(list)
    return is_list, rest_goals, [unif]


def handle_reverse(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 2 or goal.arity != 2:
        return False, [], {}

    list1, list2 = goal.params

    list1 = substitute_term(unif, list1)
    list2 = substitute_term(unif, list2)

    if is_empty_list(list1) and is_empty_list(list2):
        return True, rest_goals, [unif]

    if is_empty_list(list1):
        if isinstance(list2, Variable):
            empty_list = Struct("[]", 0, [])
            success, new_unif = match_params([list2], [empty_list], unif)
            return success, rest_goals, [new_unif] if success else []
        else:
            return is_empty_list(list2), rest_goals, [unif]

    if is_empty_list(list2):
        if isinstance(list1, Variable):
            empty_list = Struct("[]", 0, [])
            success, new_unif = match_params([list1], [empty_list], unif)
            return success, rest_goals, [new_unif] if success else []
        else:
            return is_empty_list(list1), rest_goals, [unif]

    # Case: list1 is instantiated, list2 is variable
    if not isinstance(list1, Variable) and isinstance(list2, Variable):
        list1_extr = extract_list(list1)
        if list1_extr is not None:
            reversed_list = list(reversed(list1_extr))
            reversed_struct = PrologList(reversed_list).to_struct()
            success, new_unif = match_params([list2], [reversed_struct], unif)
            return success, rest_goals, [new_unif] if success else []
        return False, [], []

    # Case: list1 is variable, list2 is instantiated
    if isinstance(list1, Variable) and not isinstance(list2, Variable):
        list2_extr = extract_list(list2)
        if list2_extr is not None:
            reversed_list = list(reversed(list2_extr))
            reversed_struct = PrologList(reversed_list).to_struct()
            success, new_unif = match_params([list1], [reversed_struct], unif)
            return success, rest_goals, [new_unif] if success else []
        return False, [], []

    # Case: both instantiated - check if one is reverse of other
    if not isinstance(list1, Variable) and not isinstance(list2, Variable):
        list1_extr = extract_list(list1)
        list2_extr = extract_list(list2)

        if list1_extr is not None and list2_extr is not None:
            return list(reversed(list1_extr)) == list2_extr, rest_goals, [unif]
        return False, [], []

    return False, [], []


def handle_subtract(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 3 or goal.arity != 3:
        return False, [], []

    set_list, delete_list, result = goal.params

    set_list = substitute_term(unif, set_list)
    delete_list = substitute_term(unif, delete_list)
    result = substitute_term(unif, result)

    if isinstance(set_list, Variable) or isinstance(delete_list, Variable):
        return False, [], []

    set_elements = extract_list(set_list)
    delete_elements = extract_list(delete_list)

    if set_elements is None or delete_elements is None:
        return False, [], []

    result_elements = []

    for set_elem in set_elements:
        should_keep = True

        for delete_elem in delete_elements:
            success, temp_unif = match_params([set_elem], [delete_elem], {})
            if success:
                should_keep = False
                break

        if should_keep:
            result_elements.append(set_elem)

    result_prolog_list = PrologList(result_elements).to_struct()
    success, new_unif = match_params([result], [result_prolog_list], unif)

    if success:
        return True, rest_goals, [new_unif]
    else:
        return False, [], []


def handle_member(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 2 or goal.arity != 2:
        raise ErrUnknownPredicate("원소", len(goal.params))

    element, list_term = goal.params
    element = substitute_term(unif, element)
    list_term = substitute_term(unif, list_term)

    if isinstance(list_term, Variable):
        raise ErrInfiniteGeneration(goal)

    all_elements = []
    current = list_term

    while True:
        if is_empty_list(current):
            break
        elif is_list_cons(current):
            head, tail = get_head_tail(current)
            all_elements.append(head)
            current = tail
        else:
            all_elements.append(current)
            break

    all_solutions = []
    for elem in all_elements:
        success, new_unif = match_params([element], [elem], unif)
        if success:
            all_solutions.append(new_unif)
    return len(all_solutions) > 0, rest_goals, all_solutions


def handle_memberchk(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 2 or goal.arity != 2:
        raise ErrUnknownPredicate("원소점검", len(goal.params))

    element, list_term = goal.params
    element = substitute_term(unif, element)
    list_term = substitute_term(unif, list_term)

    if isinstance(list_term, Variable):
        raise ErrInfiniteGeneration(goal)

    all_elements = []
    current = list_term

    while True:
        if is_empty_list(current):
            break
        elif is_list_cons(current):
            head, tail = get_head_tail(current)
            all_elements.append(head)
            current = tail
        else:
            all_elements.append(current)
            break

    all_solutions = []
    for elem in all_elements:
        success, new_unif = match_params([element], [elem], unif)
        if success:
            all_solutions.append(new_unif)
    return len(all_solutions) > 0, rest_goals, all_solutions


def handle_sort(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 2 or goal.arity != 2:
        raise ErrUnknownPredicate("정렬", len(goal.params))

    input_list, output_list = goal.params
    input_list = substitute_term(unif, input_list)
    output_list = substitute_term(unif, output_list)

    if isinstance(input_list, Variable):
        return False, rest_goals, []

    extracted = extract_list(input_list)
    if extracted is None:
        return False, rest_goals, []

    try:
        sortable_items = []
        for item in extracted:
            if isinstance(item, Struct) and item.arity == 0:
                try:
                    sortable_items.append((float(item.name), item))
                except ValueError:
                    sortable_items.append((item.name, item))
            else:
                sortable_items.append((str(item), item))

        sorted_unique = []
        seen = set()
        for key, item in sorted(sortable_items, key=lambda x: x[0]):
            item_str = str(item)
            if item_str not in seen:
                seen.add(item_str)
                sorted_unique.append(item)

        sorted_list = PrologList(sorted_unique).to_struct()
        success, new_unif = match_params([output_list], [sorted_list], unif)
        return success, rest_goals, [new_unif] if success else []

    except Exception:
        return False, rest_goals, []


def handle_keysort(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 2 or goal.arity != 2:
        raise ErrUnknownPredicate("keysort", len(goal.params))

    input_list, output_list = goal.params
    input_list = substitute_term(unif, input_list)
    output_list = substitute_term(unif, output_list)

    if isinstance(input_list, Variable):
        return False, rest_goals, []

    extracted = extract_list(input_list)
    if extracted is None:
        return False, rest_goals, []

    try:
        sortable_pairs = []
        for item in extracted:
            if (
                isinstance(item, Struct)
                and item.name == "-"
                and item.arity == 2
            ):
                key, value = item.params
                if isinstance(key, Struct) and key.arity == 0:
                    try:
                        # try numeric sorting first
                        sortable_pairs.append((float(key.name), item))
                    except ValueError:
                        # fall back to lexicographic sorting
                        sortable_pairs.append((key.name, item))
                else:
                    # for complex keys, sort by string representation
                    sortable_pairs.append((str(key), item))
            else:
                # if not a key-value pair, treat the whole item as key
                if isinstance(item, Struct) and item.arity == 0:
                    try:
                        sortable_pairs.append((float(item.name), item))
                    except ValueError:
                        sortable_pairs.append((item.name, item))
                else:
                    sortable_pairs.append((str(item), item))

        sorted_items = [
            item for key, item in sorted(sortable_pairs, key=lambda x: x[0])
        ]

        sorted_list = PrologList(sorted_items).to_struct()
        success, new_unif = match_params([output_list], [sorted_list], unif)
        return success, rest_goals, [new_unif] if success else []

    except Exception:
        return False, rest_goals, []


def handle_atom_chars(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 2:
        raise ErrUnknownPredicate("문자리스트", len(goal.params))

    atom_param, chars_param = goal.params
    atom_param = substitute_term(unif, atom_param)
    chars_param = substitute_term(unif, chars_param)

    # both are variables - error
    if isinstance(atom_param, Variable) and isinstance(chars_param, Variable):
        raise ErrUninstantiated(
            f"{atom_param.name}, {chars_param.name}", "문자리스트"
        )

    # atom is given, generate character list
    if not isinstance(atom_param, Variable):
        if not (isinstance(atom_param, Struct) and atom_param.arity == 0):
            raise ErrType(str(atom_param), "원자")

        atom_str = atom_param.name

        # strip single quotes if present
        if (
            atom_str.startswith("'")
            and atom_str.endswith("'")
            and len(atom_str) >= 2
        ):
            atom_str = atom_str[1:-1]

        # convert each character to a Struct with single quotes
        char_list = []
        for char in atom_str:
            char_list.append(Struct(f"'{char}'", 0, []))

        chars_prolog_list = PrologList(char_list).to_struct()

        success, new_unif = match_params(
            [chars_param], [chars_prolog_list], unif
        )
        return success, rest_goals, [new_unif] if success else []

    # character list is given, generate atom
    elif not isinstance(chars_param, Variable):
        if is_empty_list(chars_param):
            empty_atom = Struct("''", 0, [])
            success, new_unif = match_params([atom_param], [empty_atom], unif)
            return success, rest_goals, [new_unif] if success else []

        char_elements = []
        current = chars_param

        while True:
            if is_empty_list(current):
                break
            elif (
                isinstance(current, Struct)
                and current.name == "."
                and current.arity == 2
            ):
                head, tail = current.params

                if not (isinstance(head, Struct) and head.arity == 0):
                    raise ErrType(str(head), "문자")

                char_str = head.name
                if (
                    char_str.startswith("'")
                    and char_str.endswith("'")
                    and len(char_str) >= 2
                ):
                    char_str = char_str[1:-1]

                if len(char_str) != 1:
                    raise ErrType(head.name, "단일 문자")

                char_elements.append(char_str)
                current = tail
            else:
                raise ErrType(str(chars_param), "문자 리스트")

        atom_str = "".join(char_elements)

        if atom_str == "" or any(
            not c.isalnum() and c != "_" for c in atom_str
        ):
            atom_struct = Struct(f"'{atom_str}'", 0, [])
        else:
            atom_struct = Struct(atom_str, 0, [])

        success, new_unif = match_params([atom_param], [atom_struct], unif)
        return success, rest_goals, [new_unif] if success else []

    return False, rest_goals, []


def handle_flatten(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 2 or goal.arity != 2:
        raise ErrUnknownPredicate("평평히", len(goal.params))

    input_list, output_list = goal.params
    input_list = substitute_term(unif, input_list)
    output_list = substitute_term(unif, output_list)

    # flatten(X, Y) where both are variables
    if isinstance(input_list, Variable) and isinstance(output_list, Variable):
        result_list = PrologList([input_list]).to_struct()
        success, new_unif = match_params([output_list], [result_list], unif)
        return success, rest_goals, [new_unif] if success else []

    # flatten(X, [1,2,3]) where first is variable, second is instantiated
    if isinstance(input_list, Variable) and not isinstance(
        output_list, Variable
    ):
        return False, rest_goals, []

    # flatten([1,2,[3],[4,[5]]], X) where first is instantiated, second is variable
    if not isinstance(input_list, Variable) and isinstance(
        output_list, Variable
    ):
        try:
            flattened_elements = flatten_recursive(input_list)
            flattened_list = PrologList(flattened_elements).to_struct()
            success, new_unif = match_params(
                [output_list], [flattened_list], unif
            )
            return success, rest_goals, [new_unif] if success else []
        except:
            return False, rest_goals, []

    # flatten([1,2,3], [1,2,3]) where both are instantiated
    if not isinstance(input_list, Variable) and not isinstance(
        output_list, Variable
    ):
        try:
            flattened_elements = flatten_recursive(input_list)
            flattened_list = PrologList(flattened_elements).to_struct()
            success, _ = match_params([output_list], [flattened_list], {})
            return success, rest_goals, [unif] if success else []
        except:
            return False, rest_goals, []

    return False, rest_goals, []


def flatten_recursive(term: Term) -> List[Term]:
    if is_empty_list(term):
        return []

    if not is_list_cons(term):
        return [term]

    result = []
    current = term

    while True:
        if is_empty_list(current):
            break
        elif is_list_cons(current):
            head, tail = get_head_tail(current)

            if is_list_cons(head) or is_empty_list(head):
                flattened_head = flatten_recursive(head)
                result.extend(flattened_head)
            else:
                result.append(head)

            current = tail
        else:
            if is_list_cons(current) or is_empty_list(current):
                flattened_tail = flatten_recursive(current)
                result.extend(flattened_tail)
            else:
                result.append(current)
            break

    return result


def handle_between(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 3 or goal.arity != 3:
        print(goal.params)
        raise ErrUnknownPredicate("이내", len(goal.params))

    low_term, high_term, value = goal.params
    low_term = substitute_term(unif, low_term)
    high_term = substitute_term(unif, high_term)
    value = substitute_term(unif, value)

    if isinstance(low_term, Variable):
        raise ErrUninstantiated(low_term.name, "이내")
    if isinstance(high_term, Variable):
        raise ErrUninstantiated(high_term.name, "이내")

    try:
        low_int = int(low_term.name)
    except ValueError as e:
        raise ErrType(low_term.name, "정수") from e

    try:
        high_int = int(high_term.name)
    except ValueError as e:
        raise ErrType(high_term.name, "정수") from e

    if isinstance(value, Variable):
        all_solutions = []
        for i in range(low_int, high_int + 1):
            value_term = Struct(str(i), 0, [])
            success, new_unif = match_params([value], [value_term], unif)
            if success:
                all_solutions.append(new_unif)
        return len(all_solutions) > 0, rest_goals, all_solutions
    else:
        try:
            value_int = int(value.name)
        except ValueError as e:
            raise ErrType(value.name, "정수") from e

        if low_int <= value_int <= high_int:
            return True, rest_goals, [unif]
        else:
            return False, rest_goals, [unif]


def handle_ord_subset(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 2 or goal.arity != 2:
        raise ErrUnknownPredicate("서열부분집합", len(goal.params))

    subset, setParam = goal.params
    subset = substitute_term(unif, subset)
    setParam = substitute_term(unif, setParam)

    if isinstance(subset, Variable) and isinstance(setParam, Variable):
        raise ErrUninstantiated(
            f"{subset.name}, {setParam.name}", "서열부분집합"
        )

    if isinstance(subset, Variable):
        if not (is_list_cons(setParam) or is_empty_list(setParam)):
            raise ErrUninstantiated(
                setParam.name
                if isinstance(setParam, Variable)
                else str(setParam),
                "서열부분집합",
            )
        empty_struct = Struct("[]", 0, [])
        success, new_unif = match_params([subset], [empty_struct], unif)
        return success, rest_goals, [new_unif] if success else []

    elif isinstance(setParam, Variable):
        if not (is_list_cons(subset) or is_empty_list(subset)):
            raise ErrUninstantiated(
                subset.name if isinstance(subset, Variable) else str(subset),
                "서열부분집합",
            )

        # ord_subset([1,2,3], X) - should return X = [1,2,3|_]
        if is_empty_list(subset):
            # empty subset can match any list
            return True, rest_goals, [unif]
        else:
            # create a list structure [1,2,3|_] where _ is a variable
            subset_elements = extract_list(subset)
            if subset_elements is None:
                raise ErrUninstantiated(str(subset), "서열부분집합")

            tail_var = Variable("_")  # FIXME is hard coded right now
            result_list = PrologList(subset_elements, tail_var).to_struct()
            success, new_unif = match_params([setParam], [result_list], unif)
            return success, rest_goals, [new_unif] if success else []

    # both instantiated - check if subset is ordered subsequence of setParam
    else:
        if not (is_list_cons(subset) or is_empty_list(subset)):
            raise ErrUninstantiated(str(subset), "서열부분집합")
        if not (is_list_cons(setParam) or is_empty_list(setParam)):
            raise ErrUninstantiated(str(setParam), "서열부분집합")

        subset_elements = extract_list(subset)
        setParam_elements = extract_list(setParam)

        if subset_elements is None or setParam_elements is None:
            raise ErrUninstantiated("invalid list structure", "서열부분집합")

        if is_ordered_subsequence(subset_elements, setParam_elements):
            return True, rest_goals, [unif]
        else:
            return False, rest_goals, []


def handle_select(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 3 or goal.arity != 3:
        raise ErrUnknownPredicate("선택", len(goal.params))

    element, list_term, rest = goal.params
    element = substitute_term(unif, element)
    list_term = substitute_term(unif, list_term)
    rest = substitute_term(unif, rest)

    # list_term must be instantiated
    if isinstance(list_term, Variable):
        raise ErrUninstantiated(list_term.name, "선택")

    if is_empty_list(list_term):
        return False, rest_goals, []

    # convert list to elements for easier processing
    list_elements = []
    current = list_term
    while not is_empty_list(current) and is_list_cons(current):
        head, tail = get_head_tail(current)
        list_elements.append(head)
        current = tail

    # generate all possible selections
    all_solutions = []
    for i, list_elem in enumerate(list_elements):
        # try to unify element with this list element
        success, elem_unif = match_params([element], [list_elem], unif)
        if success:
            # create rest list by removing element at position i
            rest_elements = list_elements[:i] + list_elements[i + 1 :]
            rest_list = PrologList(rest_elements).to_struct()
            success, final_unif = match_params([rest], [rest_list], elem_unif)
            if success:
                all_solutions.append(final_unif)

    return len(all_solutions) > 0, rest_goals, all_solutions


def is_ordered_subsequence(subseq, seq):
    if not subseq:
        return True
    if not seq:
        return False

    sub_idx = 0
    for item in seq:
        if sub_idx < len(subseq):
            success, _ = match_params([subseq[sub_idx]], [item], {})
            if success:
                sub_idx += 1
                if sub_idx == len(subseq):
                    return True

    return sub_idx == len(subseq)


def generate_list(n: int) -> Term:
    if n == 0:
        return Struct("[]", 0, [])

    result = Struct("[]", 0, [])
    for i in range(n):
        var = Variable("_")
        result = Struct(".", 2, [var, result])

    return result


def is_empty_list(term: Term) -> bool:
    return isinstance(term, Struct) and term.name == "[]" and term.arity == 0


def is_list_cons(term: Term) -> bool:
    return isinstance(term, Struct) and term.name == "." and term.arity == 2


def get_head_tail(term: Term) -> Tuple[Term, Term]:
    if is_list_cons(term):
        return term.params[0], term.params[1]
    raise ErrList()
