from typing import Dict, List, Tuple

from err import (
    ErrInvalidCommand,
    ErrProlog,
    ErrSyntax,
    ErrUnknownPredicate,
    handle_error,
)
from PARSER.ast import Struct, Term, Variable
from PARSER.Data.list import PrologList, extract_list
from PARSER.parser import parse_line
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
    # Use your existing findall logic
    success, findall_goals, findall_unifs = handle_findall(
        goal, rest_goals, unif, program, debug_state
    )

    if success and findall_unifs:
        # Extract the list from findall result
        result_list = findall_unifs[0][goal.params[2].name]  # The bag
        python_list = extract_list(result_list)
        unique_sorted = sorted(set(python_list))  # Remove dups + sort

        # Convert back to Prolog list
        setof_result = PrologList(unique_sorted).to_struct()

        # Update unification
        final_unif = findall_unifs[0].copy()
        final_unif[goal.params[2].name] = setof_result

        return len(unique_sorted) > 0, rest_goals, [final_unif]  # Fail if empty

    return False, rest_goals, []


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
            (x.name == "findall" or x.name == "setof" or x.name == "->")
            or has_builtin(x.name)
        ):
            if x.name == "findall":
                success, new_goals, new_unifications = handle_findall(
                    x, rest, old_unif, program, debug_state
                )
            elif x.name == "setof":
                success, new_goals, new_unifications = handle_setof(
                    x, rest, old_unif, program, debug_state
                )
            elif x.name == "->":
                success, new_goals, new_unifications = handle_arrow(
                    x, rest, old_unif, program, debug_state
                )
            else:
                success, new_goals, new_unifications = handle_builtins(
                    x, rest, old_unif
                )
            if success:
                all_solutions = []
                i = 0
                for unif in new_unifications:
                    i += 1
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
                # seq = final_seq

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


def solve(
    program: List[List[Term]], goals: List[Term], debug_state: DebugState
) -> Tuple[bool, List[Dict[str, Term]]]:
    result, unifs = solve_with_unification(program, goals, {}, debug_state)
    clean_unifs = [
        {k: v for k, v in unif.items() if k != "__CUT_ENCOUNTERED__"}
        for unif in unifs
    ]
    return result, [
        extract_variable(get_variables(goals), u) for u in clean_unifs
    ]
