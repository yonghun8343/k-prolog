from typing import Dict, List, Tuple, Optional, Union
import copy

from err import (
    ErrInvalidCommand,
    ErrList,
    ErrProlog,
    ErrUnknownPredicate,
    handle_error,
)
from PARSER.ast import Struct, Term, Variable
from PARSER.Data.list import (
    PrologList,
    extract_list,
    is_empty_list,
)
from UTIL.debug import (
    DebugState,
    handle_trace_input,
    show_call_trace,
    show_exit_trace,
)
from UTIL.str_util import flatten_comma_structure

from .builtin import handle_builtins, has_builtin
from .unification import (
    extract_variable,
    match_params,
    substitute_term,
)


def has_delayed_constraints(goals: List[Term]) -> bool:
    for goal in goals:
        if isinstance(goal, Struct) and hasattr(goal, '_delay_count') and goal._delay_count > 0:
            return True
    return False


def contains_arithmetic_constraints(goal: Term) -> bool:
    if isinstance(goal, Struct):
        if goal.name in {">", "<", ">=", "=<", "=:=", "=\\=", "mod", "is"}:
            return True
        # recursively check parameters
        for param in goal.params:
            if contains_arithmetic_constraints(param):
                return True
    return False


def solve_goal_with_constraint_handling(
    program: List[List[Term]],
    goal: Term,
    unif: Dict[str, Term],
    debug_state: DebugState,
    max_constraint_attempts: int = 3
) -> Tuple[bool, List[Dict[str, Term]], bool]:

    # first attempt with normal solving
    success, solutions = solve_with_choice_points(
        program, [goal], unif, debug_state, []
    )
    
    if success:
        return success, solutions, False
    
    # check if the goal likely contains arithmetic constraints that might cause delays
    if contains_arithmetic_constraints(goal):
        # this goal might fail due to unresolved constraints rather than logical failure
        # in a more sophisticated implementation, we'd track the exact cause of failure
        return False, [], True  # assume unresolved constraints for arithmetic goals
    
    # for non-arithmetic goals, assume definitive failure
    return False, [], False


def get_variables(terms: List[Term]) -> List[str]:
    result = []

    for t in terms:
        if isinstance(t, Variable):
            result.append(t.name)

        elif isinstance(t, Struct):
            result.extend(get_variables(t.params))

        elif isinstance(t, list):
            result.extend(get_variables(t))

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
def init_rules(clause: List[Term], debug_state: DebugState) -> List[Term]:
    counter = debug_state.seq
    debug_state.seq += 100

    vars_in_clause = get_variables(clause)

    var_map = {}
    current_counter = counter

    for var_name in vars_in_clause:
        if var_name not in var_map:
            var_map[var_name] = Variable(f"TEMP{current_counter}")
            current_counter += 1

    renamed_clause = [substitute_term(var_map, term) for term in clause]
    return renamed_clause


def handle_findall(
    goal: Struct,
    rest_goals: List[Term],
    unif: Dict[str, Term],
    program: List[List[Term]],
    debug_state: DebugState,
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 3:
        raise ErrUnknownPredicate("모두찾기", len(goal.params))
    template, query_goal, result_bag = goal.params

    try:
        if query_goal.name == "," and query_goal.arity == 2:
            flattened_goals = flatten_comma_structure(query_goal)

        substituted_query = substitute_term(unif, query_goal)
        if (
            isinstance(substituted_query, Struct)
            and substituted_query.name == ","
            and substituted_query.arity == 2
        ):
            flattened_goals = flatten_comma_structure(substituted_query)
            success, new_unifs = solve_with_unification(
                program, flattened_goals, {}, debug_state
            )
        else:
            success, new_unifs = solve_with_unification(
                program, [substituted_query], {}, debug_state
            )

        solutions = []
        if success:
            for unif_dict in new_unifs:
                instantiated_template = substitute_term(unif_dict, template)
                solutions.append(instantiated_template)

        result_list = PrologList(solutions).to_struct()
        success, final_unif = match_params([result_bag], [result_list], unif)
        return success, rest_goals, [final_unif]

    except ErrProlog as e:
        handle_error(e, "모구찾기")
        return False, [], []


def handle_setof(goal, rest_goals, unif, program, debug_state):
    success, findall_goals, findall_unifs = handle_findall(
        goal, rest_goals, unif, program, debug_state
    )

    if success and findall_unifs:
        result_list = findall_unifs[0][goal.params[2].name]  # The bag
        python_list = extract_list(result_list)
        unique_sorted = sorted(set(python_list))  # Remove dups + sort

        setof_result = PrologList(unique_sorted).to_struct()

        final_unif = findall_unifs[0].copy()
        final_unif[goal.params[2].name] = setof_result

        return len(unique_sorted) > 0, rest_goals, [final_unif]

    return False, rest_goals, []


def handle_forall(goal, rest_goals, unif, program, debug_state):
    if len(goal.params) != 2:
        raise ErrUnknownPredicate("forall", len(goal.params))

    generator, test = goal.params
    result_var = Variable("_Result")  # temporary variable name

    findall_goal = Struct("findall", 3, [generator, generator, result_var])

    findall_success, _, findall_unifs = handle_findall(
        findall_goal, [], unif.copy(), program, debug_state
    )

    if not findall_success or not findall_unifs:
        # generator failed or had no solutions means vacuously true
        return True, rest_goals, [unif]

    result_struct = findall_unifs[0][result_var.name]
    generator_results = extract_list(result_struct)

    for result in generator_results:
        ok, test_unif = match_params([generator], [result], {})
        if not ok:
            return False, [], []

        test_instantiated = substitute_term(test_unif, test)

        success, _ = solve_with_unification(
            program, [test_instantiated], {}, debug_state
        )
        if not success:
            return False, [], []

    return True, rest_goals, [unif]


def handle_maplist(goal, rest_goals, unif, program, debug_state):
    if len(goal.params) < 2:
        raise ErrUnknownPredicate("maplist", len(goal.params))
    pred = goal.params[0]
    lists = goal.params[1:]
    lists = [substitute_term(unif, lst) for lst in lists]

    if isinstance(lists[0], list):
        lists = lists[0]

    if all(is_empty_list(lst) for lst in lists):
        return True, rest_goals, [unif]

    if any(is_empty_list(lst) for lst in lists) and not all(
        is_empty_list(lst) for lst in lists
    ):
        return False, [], []

    try:
        heads = []
        tails = []
        for lst in lists:
            if not isinstance(lst, Struct) or lst.name != ".":
                return False, rest_goals, []
            heads.append(lst.params[0])
            tails.append(lst.params[1])
    except ErrList:
        return False, [], []

    if isinstance(pred, Struct):
        pred_call = Struct(pred.name, len(heads), heads)
    else:
        pred_call = Struct(str(pred), len(heads), heads)

    success, new_unifs = solve_with_unification(
        program, [pred_call], unif, debug_state
    )
    if not success or not new_unifs:
        return False, [], []

    new_unif = new_unifs[0]

    recursive_goal = Struct("maplist", len(lists) + 1, [pred] + tails)
    return handle_maplist(
        recursive_goal, rest_goals, new_unif, program, debug_state
    )


def handle_arrow(
    goal: Struct,
    rest_goals: List[Term],
    unif: Dict[str, Term],
    program: List[List[Term]],
    debug_state: DebugState,
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) not in [2, 3]:
        raise ErrUnknownPredicate("->", len(goal.params))

    try:
        success, new_unifs = solve_with_unification(
            program, [goal.params[0]], unif, debug_state
        )

        if success:
            condition_unif = new_unifs[0] if new_unifs else unif
            then_success, then_unifs = solve_with_unification(
                program, [goal.params[1]], condition_unif, debug_state
            )
            return then_success, rest_goals, then_unifs
        else:
            if len(goal.params) == 3:
                else_success, else_unifs = solve_with_unification(
                    program, [goal.params[2]], unif, debug_state
                )
                return else_success, rest_goals, else_unifs
            else:
                return False, rest_goals, []

    except ErrProlog as e:
        handle_error(e, "-> predicate")
        return False, rest_goals, []


def solve_with_unification(
    program: List[List[Term]],
    goals: List[Term],
    old_unif: Dict[str, Term],
    debug_state: DebugState,
) -> Tuple[bool, List[Dict[str, Term]]]:
    if not goals:
        return True, [old_unif]
    x, *rest = goals
    if debug_state.trace_mode:
        show_call_trace(x, debug_state.call_depth)
        handle_trace_input(debug_state)

    debug_state.call_depth += 1

    try:
        if isinstance(x, Struct) and x.name == "," and x.arity == 2:
            flattened_goals = flatten_comma_structure(x)
            return solve_with_unification(
                program, flattened_goals + rest, old_unif, debug_state
            )
        if (
            isinstance(x, Struct)
            and ((x.name == "fail") or (x.name == "포기"))
            and x.arity == 0
        ):
            if debug_state.trace_mode:
                show_call_trace(x, debug_state.call_depth - 1)
                handle_trace_input(debug_state)
            return False, []

        if isinstance(x, Struct) and x.name == "!" and x.arity == 0:
            success, solutions = solve_with_unification(
                program,
                rest,
                old_unif,
                debug_state,
            )
            if success:
                marked_solutions = []
                for solution in solutions:
                    marked_solution = solution.copy()
                    marked_solution["__CUT_ENCOUNTERED__"] = True
                    marked_solutions.append(marked_solution)
                return True, marked_solutions
            else:
                cut_marker = old_unif.copy()
                cut_marker["__CUT_ENCOUNTERED__"] = True
                return False, [cut_marker]

        if isinstance(x, Struct) and (
            (x.name == "not") or (x.name == "논리부정")
        ):
            if not len(x.params) == 1:
                raise ErrInvalidCommand(f"{x.__repr__()}")

            inner_goal = substitute_term(old_unif, x.params[0])
            success, solutions = solve_with_unification(
                program,
                [inner_goal],
                old_unif,
                debug_state,
            )
            if success:
                return False, []
            else:
                if debug_state.trace_mode:
                    show_exit_trace(x, debug_state.call_depth - 1)
                    handle_trace_input(debug_state)

                return solve_with_unification(
                    program, rest, old_unif, debug_state
                )

        if isinstance(x, Struct) and (
            x.name in {"findall", "setof", "forall", "maplist", "->"}
            or has_builtin(x.name)
        ):
            internal_handlers = {
                "findall": handle_findall,
                "setof": handle_setof,
                "forall": handle_forall,
                "maplist": handle_maplist,
                "->": handle_arrow,
            }
            if x.name in internal_handlers:
                success, new_goals, new_unifications = internal_handlers.get(
                    x.name
                )(x, rest, old_unif, program, debug_state)
            else:
                success, new_goals, new_unifications = handle_builtins(
                    x, rest, old_unif
                )
            if success:
                all_solutions = []
                for unif in new_unifications:
                    success, solutions = solve_with_unification(
                        program,
                        new_goals,
                        unif,
                        debug_state,
                    )

                    if success:
                        all_solutions.extend(solutions)
                        if any(
                            "__CUT_ENCOUNTERED__" in solution
                            for solution in solutions
                        ):
                            clean_solutions = [
                                {
                                    k: v
                                    for k, v in sol.items()
                                    if k != "__CUT_ENCOUNTERED__"
                                }
                                for sol in all_solutions
                            ]
                            return True, clean_solutions

                if debug_state.trace_mode and all_solutions:
                    show_exit_trace(x, debug_state.call_depth - 1)
                    handle_trace_input(debug_state)

                return bool(all_solutions), all_solutions

        clauses = [c for c in program if is_relevant(x, c)]
        all_solutions = []

        for clause in clauses:
            debug_state.seq += 1000
            renamed_clause = init_rules(clause, debug_state)
            # seq = new_seq
            is_match, new_goals, unif = match_predicate(
                x, rest, old_unif, renamed_clause
            )

            if is_match:
                success, solutions = solve_with_unification(
                    program,
                    new_goals,
                    unif,
                    debug_state,
                )

                if any(
                    "__CUT_ENCOUNTERED__" in solution for solution in solutions
                ):
                    if success:
                        all_solutions.extend(solutions)

                    return success, solutions
                if success:
                    all_solutions.extend(solutions)

        if debug_state.trace_mode and all_solutions:
            show_exit_trace(x, debug_state.call_depth - 1)
            handle_trace_input(debug_state)

        return bool(all_solutions), all_solutions

    finally:
        debug_state.call_depth -= 1


class ChoicePoint:
    alternatives: List[
        Union[List[Term], Dict[str, Term]]
    ]  # clauses or unifications
    current_index: int
    goal: Term
    rest_goals: List[Term]
    new_goals: List[Term]
    base_unif: Dict[str, Term]
    call_depth: int

    def __init__(
        self,
        alternatives,
        current_index,
        goal,
        rest_goals,
        new_goals,
        base_unif,
        call_depth,
    ):
        self.alternatives = alternatives
        self.current_index = current_index
        self.goal = goal
        self.rest_goals = rest_goals
        self.new_goals = new_goals
        self.base_unif = base_unif
        self.call_depth = call_depth


def solve_with_choice_points(
    program: List[List[Term]],
    goals: List[Term],
    unif: Dict[str, Term],
    debug_state: DebugState,
    choice_stack: Optional[List[ChoicePoint]] = None,
) -> Tuple[bool, List[Dict[str, Term]]]:
    if choice_stack is None:
        choice_stack = []

    all_solutions = []  
    # main solving loop - replaces recursion with iteration
    while True:
        if not goals:
            all_solutions.append(unif.copy())

            backtrack_result = backtrack(program, choice_stack, debug_state)
            if backtrack_result is None:
                return len(all_solutions) > 0, all_solutions
            goals, unif = backtrack_result
            continue

        x, *rest = goals

        if debug_state.trace_mode:
            show_call_trace(x, debug_state.call_depth)
            handle_trace_input(debug_state)

        debug_state.call_depth += 1

        try:
            if isinstance(x, Struct) and x.name == "," and x.arity == 2:
                flattened_goals = flatten_comma_structure(x)
                goals = flattened_goals + rest
                continue

            if (
                isinstance(x, Struct)
                and ((x.name == "fail") or (x.name == "포기"))
                and x.arity == 0
            ):
                if debug_state.trace_mode:
                    show_call_trace(x, debug_state.call_depth - 1)
                    handle_trace_input(debug_state)

                backtrack_result = backtrack(program, choice_stack, debug_state)
                if backtrack_result is None:
                    return len(all_solutions) > 0, all_solutions
                goals, unif = backtrack_result
                continue

            if isinstance(x, Struct) and x.name == "!" and x.arity == 0:
                choice_stack.clear()
                goals = rest
                continue

            if isinstance(x, Struct) and (
                x.name == "not" or x.name == "논리부정"
            ):
                if not len(x.params) == 1:
                    raise ErrInvalidCommand(f"{x.__repr__()}")

                inner_goal = substitute_term(unif, x.params[0])

                inner_success, _, has_unresolved = solve_goal_with_constraint_handling(
                    program, inner_goal, unif, debug_state
                )

                if inner_success:
                    backtrack_result = backtrack(
                        program, choice_stack, debug_state
                    )
                    if backtrack_result is None:
                        return len(all_solutions) > 0, all_solutions
                    goals, unif = backtrack_result
                    continue
                elif has_unresolved:
                    if len(rest) > 0:
                        # try to delay this negation goal
                        delay_count = getattr(x, '_delay_count', 0)
                        if delay_count < 3:
                            x._delay_count = delay_count + 1
                            goals = rest + [x]
                            continue
                    
                    # can't delay further - fail with backtrack
                    backtrack_result = backtrack(
                        program, choice_stack, debug_state
                    )
                    if backtrack_result is None:
                        return len(all_solutions) > 0, all_solutions
                    goals, unif = backtrack_result
                    continue
                else:
                    if debug_state.trace_mode:
                        show_exit_trace(x, debug_state.call_depth - 1)
                        handle_trace_input(debug_state)
                    goals = rest
                    continue

            if isinstance(x, Struct) and (
                x.name in {"findall", "setof", "forall", "maplist", "->"}
                or has_builtin(x.name)
            ):
                internal_handlers = {
                    "findall": handle_findall,
                    "setof": handle_setof,
                    "forall": handle_forall,
                    "maplist": handle_maplist,
                    "->": handle_arrow,
                }

                if x.name in internal_handlers:
                    success, new_goals, new_unifications = internal_handlers[
                        x.name
                    ](x, rest, unif, program, debug_state)
                else:
                    success, new_goals, new_unifications = handle_builtins(
                        x, rest, unif
                    )

                if success and new_unifications:
                    if len(new_unifications) > 1:
                        choice_point = ChoicePoint(
                            alternatives=new_unifications[
                                1:
                            ],  # store remaining unifications
                            current_index=0,
                            goal=x,
                            rest_goals=rest,
                            new_goals=new_goals,
                            base_unif=unif,
                            call_depth=debug_state.call_depth,
                        )
                        choice_stack.append(choice_point)
                    goals = new_goals
                    unif = new_unifications[0]
                    continue
                else:
                    backtrack_result = backtrack(
                        program, choice_stack, debug_state
                    )
                    if backtrack_result is None:
                        return len(all_solutions) > 0, all_solutions
                    goals, unif = backtrack_result
                    continue

            clauses = [c for c in program if is_relevant(x, c)]

            if not clauses:
                backtrack_result = backtrack(program, choice_stack, debug_state)
                if backtrack_result is None:
                    return len(all_solutions) > 0, all_solutions
                goals, unif = backtrack_result
                continue

            first_clause = clauses[0]
            debug_state.seq += 1000
            renamed_clause = init_rules(first_clause, debug_state)

            is_match, new_goals, new_unif = match_predicate(
                x, rest, unif, renamed_clause
            )

            if is_match:
                # create choice point if there are more clauses
                if len(clauses) > 1:
                    choice_point = ChoicePoint(
                        alternatives=clauses[1:],
                        current_index=0,
                        goal=x,
                        rest_goals=rest,
                        new_goals=rest,
                        base_unif=unif,
                        call_depth=debug_state.call_depth,
                    )
                    choice_stack.append(choice_point)

                goals = new_goals
                unif = new_unif
                continue
            else:
                if len(clauses) > 1:
                    choice_point = ChoicePoint(
                        alternatives=clauses[1:],
                        current_index=0,
                        goal=x,
                        rest_goals=rest,
                        new_goals=rest,
                        base_unif=unif,
                        call_depth=debug_state.call_depth,
                    )
                    backtrack_result = try_next_alternative(
                        program, choice_point, choice_stack, debug_state
                    )
                    if backtrack_result is not None:
                        goals, unif = backtrack_result
                        continue

                backtrack_result = backtrack(program, choice_stack, debug_state)
                if backtrack_result is None:
                    return len(all_solutions) > 0, all_solutions
                goals, unif = backtrack_result
                continue

        finally:
            debug_state.call_depth -= 1


def try_next_alternative(
    program: List[List[Term]],
    choice_point: ChoicePoint,
    choice_stack: List[ChoicePoint],
    debug_state: DebugState,
) -> Optional[Tuple[List[Term], Dict[str, Term]]]:

    while choice_point.current_index < len(choice_point.alternatives):
        alternative = choice_point.alternatives[choice_point.current_index]
        choice_point.current_index += 1

        if isinstance(alternative, list):  # clause
            debug_state.seq += 1000
            renamed_clause = init_rules(alternative, debug_state)

            is_match, new_goals, new_unif = match_predicate(
                choice_point.goal,
                choice_point.rest_goals,
                choice_point.base_unif,
                renamed_clause,
            )

            if is_match:
                # put choice point back if there are more alternatives
                if choice_point.current_index < len(choice_point.alternatives):
                    choice_stack.append(choice_point)
                return new_goals, new_unif

        else: # unification (Dict[str, Term])
            # put choice point back if there are more alternatives
            if choice_point.current_index < len(choice_point.alternatives):
                choice_stack.append(choice_point)
            return choice_point.new_goals, alternative

    return None


def backtrack(
    program: List[List[Term]],
    choice_stack: List[ChoicePoint],
    debug_state: DebugState,
) -> Optional[Tuple[List[Term], Dict[str, Term]]]:

    while choice_stack:
        choice_point = choice_stack.pop()

        debug_state.call_depth = choice_point.call_depth

        result = try_next_alternative(
            program, choice_point, choice_stack, debug_state
        )
        if result is not None:
            return result

    return None


def solve(
    program: List[List[Term]], goals: List[Term], debug_state: DebugState
) -> Tuple[bool, List[Dict[str, Term]]]:

    result, unifs = solve_with_choice_points(program, goals, {}, debug_state)
    return result, [extract_variable(get_variables(goals), u) for u in unifs]


# def solve(
#     program: List[List[Term]], goals: List[Term], debug_state: DebugState
# ) -> Tuple[bool, List[Dict[str, Term]]]:
#     result, unifs = solve_with_unification(program, goals, {}, debug_state)
#     clean_unifs = [
#         {k: v for k, v in unif.items() if k != "__CUT_ENCOUNTERED__"}
#         for unif in unifs
#     ]
#     return result, [
#         extract_variable(get_variables(goals), u) for u in clean_unifs
#     ]
