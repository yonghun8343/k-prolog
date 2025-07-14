from typing import Dict, List, Tuple

from err import ErrInvalidCommand, ErrSyntax
from PARSER.ast import Struct, Term, Variable
from UTIL.debug import (
    DebugState,
    handle_trace_input,
    show_call_trace,
    show_exit_trace,
)

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
    debug_state: DebugState,
) -> Tuple[bool, List[Dict[str, Term]], int]:
    if not goals:
        return True, [old_unif], seq
    x, *rest = goals

    if debug_state.trace_mode:
        show_call_trace(x, debug_state.call_depth)
        handle_trace_input(debug_state)

    debug_state.call_depth += 1

    try:
        if isinstance(x, Struct) and x.name == "!" and x.arity == 0:
            success, solutions, final_seq = solve_with_unification(
                program,
                rest,
                old_unif,
                seq,
                debug_state,
            )
            if success:
                if debug_state.trace_mode:
                    show_exit_trace(x, debug_state.call_depth - 1)
                    handle_trace_input()

                marked_solutions = []
                for solution in solutions:
                    marked_solution = solution.copy()
                    marked_solution["__CUT_ENCOUNTERED__"] = True
                    marked_solutions.append(marked_solution)
                return True, marked_solutions, final_seq
            else:
                return False, [], final_seq

        if isinstance(x, Struct) and x.name == "not":
            if not len(x.params) == 1:
                raise ErrInvalidCommand(f"{x.__repr__()}")

            inner_goal = substitute_term(old_unif, x.params[0])
            success, solutions, final_seq = solve_with_unification(
                program,
                [inner_goal],
                old_unif,
                seq,
                debug_state,
            )
            if success:
                return False, [], final_seq
            else:
                if debug_state.trace_mode:
                    show_exit_trace(x, debug_state.call_depth - 1)
                    handle_trace_input()

                return solve_with_unification(
                    program, rest, old_unif, final_seq, debug_state
                )

        if isinstance(x, Struct) and has_builtin(x.name):
            success, new_goals, new_unifications = handle_builtins(
                x, rest, old_unif
            )
            if success:
                all_solutions = []
                for unif in new_unifications:
                    success, solutions, final_seq = solve_with_unification(
                        program,
                        new_goals,
                        unif,
                        seq,
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
                            return True, clean_solutions, final_seq

                if debug_state.trace_mode and all_solutions:
                    show_exit_trace(x, debug_state.call_depth - 1)
                    handle_trace_input()

                return bool(all_solutions), all_solutions, seq

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
                    program,
                    new_goals,
                    unif,
                    seq,
                    debug_state,
                )
                seq = final_seq

                if success:
                    all_solutions.extend(solutions)

                    if any(
                        "__CUT_ENCOUNTERED__" in solution
                        for solution in solutions
                    ):
                        clean_solutions = []
                        for solution in all_solutions:
                            clean_sol = {
                                k: v
                                for k, v in solution.items()
                                if k != "__CUT_ENCOUNTERED__"
                            }
                            clean_solutions.append(clean_sol)
                        return True, clean_solutions, final_seq

        if debug_state.trace_mode and all_solutions:
            show_exit_trace(x, debug_state.call_depth - 1)
            handle_trace_input(debug_state)

        return bool(all_solutions), all_solutions, seq

    finally:
        debug_state.call_depth -= 1


def solve(
    program: List[List[Term]], goals: List[Term], debug_state: DebugState
) -> Tuple[bool, List[Dict[str, Term]]]:
    result, unifs, _ = solve_with_unification(
        program, goals, {}, 0, debug_state
    )
    return result, [extract_variable(get_variables(goals), u) for u in unifs]
