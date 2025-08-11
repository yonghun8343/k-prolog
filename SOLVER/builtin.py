# coding: utf-8
from typing import Dict, List, Tuple

from err import (
    AssertException,
    ErrArithmetic,
    ErrDivisionByZero,
    ErrNotNumber,
    ErrParsing,
    ErrProlog,
    ErrUninstantiated,
    ErrUnknownOperator,
    ErrUnknownPredicate,
    ErrType,
    handle_error,
)
from PARSER.ast import Struct, Term, Variable
from PARSER.Data.list import (
    handle_list_append,
    handle_list_length,
    handle_list_permutation,
    handle_is_list,
    handle_reverse,
    handle_subtract,
    handle_member
)
from PARSER.parser import parse_struct
from UTIL.str_util import struct_to_infix

from .unification import extract_variable, match_params, substitute_term


def handle_is(
    goal: Struct, rest_goals: List[Term], old_unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 2:
        raise ErrUnknownPredicate(":=", len(goal.params))

    left, right = goal.params
    try:
        result = evaluate_arithmetic(right, old_unif)

        if isinstance(result, Variable):
            raise ErrUninstantiated(result.name, "산술 표현식")

        result_term = Struct(
            str(int(result) if result.is_integer() else result), 0, []
        )

        success, new_unif = match_params([left], [result_term], old_unif)
        return success, rest_goals, [new_unif] if success else []

    except ErrProlog as e:
        handle_error(e, ":= 내장함수")
        return False, [], []


def evaluate_arithmetic(expr: Term, unif: Dict[str, Term]) -> float:
    expr = substitute_term(unif, expr)

    if isinstance(expr, Variable):
        raise ErrUninstantiated(expr.name, "산술 표현식")
    elif isinstance(expr, Struct):
        if expr.arity == 0:
            try:
                return float(expr.name)
            except ValueError as e:
                raise ErrNotNumber(expr.name) from e
        elif expr.arity == 2:
            left_val = evaluate_arithmetic(expr.params[0], unif)
            right_val = evaluate_arithmetic(expr.params[1], unif)
            if expr.name == "+":
                return left_val + right_val
            elif expr.name == "-":
                return left_val - right_val
            elif expr.name == "*":
                return left_val * right_val
            elif expr.name == "/":
                if right_val == 0:
                    raise ErrDivisionByZero()
                return left_val / right_val
            elif expr.name == "//":
                if right_val == 0:
                    raise ErrDivisionByZero()
                return float(int(left_val // right_val))
            elif expr.name == "나머지" or expr.name == "mod":
                if right_val == 0:
                    raise ErrDivisionByZero()
                return left_val % right_val
            else:
                raise ErrUnknownOperator(expr.name)
        elif expr.arity == 1:
            val = evaluate_arithmetic(expr.params[0], unif)
            if expr.name == "-":
                return -val
            elif expr.name == "+":
                return val
            else:
                raise ErrUnknownOperator(expr.name)

        else:
            raise ErrArithmetic(expr.name)

    return None


def handle_comparison(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 2:
        raise ErrUnknownPredicate(goal.name, len(goal.params))

    left, right = goal.params
    try:
        left = evaluate_arithmetic(left, unif)
        right = evaluate_arithmetic(right, unif)

    except ErrProlog as e:
        if isinstance(e, ErrUninstantiated):
            # check if this constraint has been delayed before
            delay_count = getattr(goal, "_delay_count", 0)

            if delay_count >= 3 or len(rest_goals) == 0:
                handle_error(e, "산술 계산")
                return False, [], []

            # mark this goal as delayed and move to end
            goal._delay_count = delay_count + 1
            delayed_goals = rest_goals + [goal]
            return True, delayed_goals, [unif]
        else:
            handle_error(e, "산술 계산")
            return False, [], []

    if goal.name == ">":
        success = left > right
    elif goal.name == "<":
        success = left < right
    elif goal.name == ">=":
        success = left >= right
    elif goal.name == "=<":
        success = left <= right
    elif goal.name == "=:=":
        success = left == right
    elif goal.name == "=\=":
        success = left != right
    else:
        return False, [], []

    return success, rest_goals, [unif]


def handle_equals(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 2:
        raise ErrUnknownPredicate("=", len(goal.params))

    left, right = goal.params

    success, new_unif = match_params([left], [right], unif)
    return success, rest_goals, [new_unif] if success else []


def handle_not_equals(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 2:
        raise ErrUnknownPredicate("\\=", len(goal.params))

    left, right = goal.params

    success, new_unif = match_params([left], [right], unif)

    if success:
        return False, rest_goals, []
    else:
        return True, rest_goals, [unif]


def handle_write(  # need to take care of string
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 1:
        raise ErrUnknownPredicate("쓰기", len(goal.params))

    writeStr = str(goal.params[0])
    new_unif = extract_variable([writeStr], unif)
    if new_unif:
        print(new_unif.get(writeStr))
        return True, rest_goals, [unif]

    if writeStr.startswith('"') and writeStr.endswith('"'):
        print(writeStr[1:-1])
        return True, rest_goals, [unif]

    if writeStr.startswith('"') or writeStr.endswith('"'):
        raise ErrParsing(f"{writeStr}")

    if writeStr.startswith("'") and writeStr.endswith("'"):
        print(writeStr[1:-1])
        return True, rest_goals, [unif]

    if writeStr.startswith("'") or writeStr.endswith("'"):
        raise ErrParsing({writeStr})

    struct_form = parse_struct(writeStr)
    print(struct_to_infix(struct_form))
    return True, rest_goals, [unif]


def handle_display(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 1:
        raise ErrUnknownPredicate("display", len(goal.params))

    writeStr = str(goal.params[0])
    new_unif = extract_variable([writeStr], unif)
    if new_unif:
        value = new_unif.get(writeStr)
        print(value, end="")
        return True, rest_goals, [unif]

    if writeStr.startswith('"') and writeStr.endswith('"'):
        print(writeStr[1:-1], end="")
        return True, rest_goals, [unif]

    if writeStr.startswith('"') or writeStr.endswith('"'):
        raise ErrParsing(f"{writeStr}")

    if writeStr.startswith("'") and writeStr.endswith("'"):
        print(writeStr[1:-1], end="")
        return True, rest_goals, [unif]

    if writeStr.startswith("'") or writeStr.endswith("'"):
        raise ErrParsing({writeStr})

    struct_form = parse_struct(writeStr)
    print(struct_form, end="")
    return True, rest_goals, [unif]


def handle_read(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 1:
        raise ErrUnknownPredicate("읽기", len(goal.params))

    var = goal.params[0]

    if not isinstance(var, Variable):
        return False, rest_goals, []

    lines = []
    while True:
        try:
            line = input("|: ")
            lines.append(line)
            if line.strip().endswith("."):
                break
        except EOFError:
            return False, rest_goals, []

    full_input = " ".join(line.strip() for line in lines)
    if full_input.endswith("."):
        full_input = full_input[:-1]

    full_input = full_input.strip()

    if not full_input:
        return False, rest_goals, []

    input_term = Struct(full_input, 0, [])

    success, new_unif = match_params([var], [input_term], unif)

    if success:
        return True, rest_goals, [new_unif]
    else:
        return False, rest_goals, []


def handle_atomic(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 1:
        raise ErrUnknownPredicate("단순", len(goal.params))

    param = goal.params[0]
    if (
        isinstance(param, Variable)
        or param.name[0].isupper()
        or param.name[0] == "_"
        or param.arity != 0
    ):
        return False, [], []

    return True, rest_goals, [unif]


def handle_integer(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 1:
        raise ErrUnknownPredicate("정수", len(goal.params))

    try:
        int(goal.params[0].name)
        return True, rest_goals, [unif]
    except ValueError:
        return False, [], []


def handle_nl(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 0:
        raise ErrUnknownPredicate("줄바꿈", len(goal.params))

    print()
    return True, rest_goals, [unif]


def handle_writeln(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 1:
        raise ErrUnknownPredicate("쓰고줄바꿈", len(goal.params))

    success, goals, new_unif = handle_write(goal, rest_goals, unif)
    # print()

    return success, goals, new_unif


def handle_number(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 1:
        raise ErrUnknownPredicate("수", len(goal.params))

    if goal.params[0].name.isnumeric():
        return True, rest_goals, [unif]

    return False, rest_goals, [unif]


def handle_nonvar(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 1:
        raise ErrUnknownPredicate("변수아닌가", len(goal.params))

    if isinstance(goal.params[0], Variable):
        return False, rest_goals, [unif]

    return True, rest_goals, [unif]


def handle_true(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    return True, rest_goals, [unif]


def handle_false(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    return False, [], []


def handle_atom_concat(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 3 or goal.arity != 3:
        raise ErrUnknownPredicate(goal.name, len(goal.params))

    l1, l2, l3 = goal.params
    l1 = substitute_term(unif, l1)
    l2 = substitute_term(unif, l2)
    l3 = substitute_term(unif, l3)

    def create_quoted_atom(value: str) -> Struct:
        if value == "":
            return Struct("''", 0, [])
        else:
            return Struct(f"'{value}'", 0, [])

    if isinstance(l3, Variable):
        if isinstance(l1, Variable) or isinstance(l2, Variable):
            raise ErrUninstantiated(
                "atom_concat", "적어도 2개의 인수가 인스턴스화되어야 합니다"
            )
        if not (isinstance(l1, Struct) and l1.arity == 0) or not (
            isinstance(l2, Struct) and l2.arity == 0
        ):
            raise ErrType("atom_concat는 원자가 필요합니다")

        # Extract the actual values (remove quotes if present)
        l1_val = (
            l1.name.strip("'")
            if l1.name.startswith("'") and l1.name.endswith("'")
            else l1.name
        )
        l2_val = (
            l2.name.strip("'")
            if l2.name.startswith("'") and l2.name.endswith("'")
            else l2.name
        )
        concat_val = l1_val + l2_val

        concat_struct = create_quoted_atom(concat_val)
        success, new_unif = match_params([l3], [concat_struct], unif)
        return success, rest_goals, [new_unif] if success else []
    else:
        if not (isinstance(l3, Struct) and l3.arity == 0):
            raise ErrType("atom_concat는 원자가 필요합니다")

        # Extract the actual value from l3 (remove quotes if present)
        l3_val = (
            l3.name.strip("'")
            if l3.name.startswith("'") and l3.name.endswith("'")
            else l3.name
        )

        if isinstance(l1, Variable) and isinstance(l2, Variable):
            all_unifs = []
            for i in range(len(l3_val) + 1):
                l1_part = l3_val[:i]
                l2_part = l3_val[i:]

                l1_struct = create_quoted_atom(l1_part)
                l2_struct = create_quoted_atom(l2_part)

                success1, temp_unif = match_params([l1], [l1_struct], unif)
                if success1:
                    success2, final_unif = match_params(
                        [l2], [l2_struct], temp_unif
                    )
                    if success2:
                        all_unifs.append(final_unif)

            return len(all_unifs) > 0, rest_goals, all_unifs
        elif isinstance(l1, Variable):
            if not (isinstance(l2, Struct) and l2.arity == 0):
                raise ErrType("atom_concat는 원자가 필요합니다")

            l2_val = (
                l2.name.strip("'")
                if l2.name.startswith("'") and l2.name.endswith("'")
                else l2.name
            )
            if l3_val.endswith(l2_val):
                l1_part = l3_val[: -len(l2_val)] if len(l2_val) > 0 else l3_val
                l1_struct = create_quoted_atom(l1_part)
                success, new_unif = match_params([l1], [l1_struct], unif)
                return success, rest_goals, [new_unif] if success else []
            else:
                return False, rest_goals, []
        elif isinstance(l2, Variable):
            if not (isinstance(l1, Struct) and l1.arity == 0):
                raise ErrType("atom_concat는 원자가 필요합니다")

            l1_val = (
                l1.name.strip("'")
                if l1.name.startswith("'") and l1.name.endswith("'")
                else l1.name
            )
            if l3_val.startswith(l1_val):
                l2_part = l3_val[len(l1_val) :]
                l2_struct = create_quoted_atom(l2_part)
                success, new_unif = match_params([l2], [l2_struct], unif)
                return success, rest_goals, [new_unif] if success else []
            else:
                return False, rest_goals, []
        else:
            # All three are atoms - check if l1 + l2 = l3
            if not (isinstance(l1, Struct) and l1.arity == 0) or not (
                isinstance(l2, Struct) and l2.arity == 0
            ):
                raise ErrType("atom_concat는 원자가 필요합니다")

            l1_val = (
                l1.name.strip("'")
                if l1.name.startswith("'") and l1.name.endswith("'")
                else l1.name
            )
            l2_val = (
                l2.name.strip("'")
                if l2.name.startswith("'") and l2.name.endswith("'")
                else l2.name
            )
            concat_result = l1_val + l2_val

            if concat_result == l3_val:
                return True, rest_goals, [unif]
            else:
                return False, rest_goals, []


def handle_asserta(
    goal: Struct, rest_goals: List[Term], unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if len(goal.params) != 1:
        raise ErrUnknownPredicate("asserta", len(goal.params))

    clause_term = substitute_term(unif, goal.params[0])

    if isinstance(clause_term, Variable):
        raise ErrUninstantiated(clause_term.name, "추가")

    raise AssertException(clause_term, "asserta")


BUILTINS = {
    "halt": None,
    "종료": None,
    "true": handle_true,
    "참": handle_true,
    "false": handle_false,
    "거짓": handle_false,
    "is": handle_is,
    ":=": handle_is,
    ">": handle_comparison,
    "<": handle_comparison,
    ">=": handle_comparison,
    "=<": handle_comparison,
    "=:=": handle_comparison,
    "=\=": handle_comparison,
    "=": handle_equals,
    "\=": handle_not_equals,
    "append": handle_list_append,
    "접합": handle_list_append,
    "length": handle_list_length,
    "길이": handle_list_length,
    "permutation": handle_list_permutation,
    "순열": handle_list_permutation,
    "is_list": handle_is_list,
    "리스트인가": handle_is_list,
    "reverse": handle_reverse,
    "거꾸로": handle_reverse,
    "subtract": handle_subtract,
    "원소제거": handle_subtract,
    "write": handle_write,
    "쓰기": handle_write,
    "display": handle_display,
    "출력에쓰기": handle_display,
    "writeln": handle_writeln,
    "쓰고줄바꿈": handle_writeln,
    "read": handle_read,
    "읽기": handle_read,
    "atomic": handle_atomic,
    "상수인가": handle_atomic,
    "integer": handle_integer,
    "정수인가": handle_integer,
    "nl": handle_nl,
    "줄바꿈": handle_nl,
    "number": handle_number,
    "수": handle_number,
    "nonvar": handle_nonvar,
    "변수아닌가": handle_nonvar,
    "atom_concat": handle_atom_concat,
    "산수연결": handle_atom_concat,
    "asserta": handle_asserta,
    "추가": handle_asserta,
    "member": handle_member,
    "원소" : handle_member
}


def has_builtin(builtin: str) -> bool:
    return builtin in BUILTINS


def handle_builtins(
    goal: Struct, rest_goals: List[Term], old_unif: Dict[str, Term]
) -> Tuple[bool, List[Term], List[Dict[str, Term]]]:
    if goal.name == "halt" or goal.name == "종료":
        if goal.arity == 0:
            import sys

            sys.exit(0)
        else:
            raise ErrUnknownPredicate("종료", goal.arity)

    if goal.name not in BUILTINS:
        return False, [], []
    return BUILTINS[goal.name](goal, rest_goals, old_unif)
