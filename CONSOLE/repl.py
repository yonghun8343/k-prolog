import sys
from typing import List, Tuple

from err import (
    ErrFileNotFound,
    ErrInvalidCommand,
    ErrOperator,
    ErrPeriod,
    ErrProlog,
    ErrSyntax,
    ErrUnknownPredicate,
    handle_error,
)
from PARSER.ast import Struct, Term
from PARSER.parser import parse_string
from SOLVER.solver import solve
from UTIL.debug import DebugState
from UTIL.str_util import flatten_comma_structure, format_term


class Command:
    pass


class Load(Command):
    def __init__(self, path: str):
        if "." not in path:
            path += ".pl"  # TODO hardcoded right now
        self.path = path


class Make(Command):
    pass


class Listing(Command):
    def __init__(self, predicate: str):
        self.predicate_name = predicate


class Query(Command):
    def __init__(self, query: str):
        self.query = query


class Halt(Command):
    pass


class Trace(Command):
    pass


class NoTrace(Command):
    pass


def read_multi_line_input() -> str:
    lines = []
    while True:
        try:
            if not lines:
                line = input("?- ")
            else:
                line = input("   ")

            lines.append(line)

            if line.strip().endswith("."):
                break

        except EOFError as e:
            if lines:
                raise ErrPeriod("") from e
            else:
                raise e

    full_input = " ".join(line.strip() for line in lines)
    return full_input


def parse_command(command: str) -> Command:
    if command.startswith("[") and command.endswith("]."):
        return Load(command[1:-2])
    elif command.startswith("consult(") and command.endswith(")."):
        return Load(command[8:-2])
    elif command == "make." or command == "재적재.":
        return Make()
    elif command == "halt." or command == "종료.":
        return Halt()
    elif command == "trace." or command == "추적.":
        return Trace()
    elif command == "notrace." or command == "추적중단.":
        return NoTrace()
    elif command.startswith("listing") or command.startswith("목록"):
        if command == "listing." or command == "목록":
            return Listing("none")
        elif (command.startswith("listing(") and command.endswith(").")) or (
            command.startswith("목록") and command.endswith(").")
        ):
            return Listing(command[8:-2])
        else:
            raise ErrInvalidCommand(command)
    else:
        return Query(command)


def parse_file_multiline(
    filepath: str, debug_state
) -> Tuple[List[List[Term]], List]:
    with open(filepath, "r") as f:
        content = f.read()
    pending_goals = []
    statements = []
    current_statement = ""

    i = 0
    while i < len(content):
        char = content[i]
        if char == "%":
            while i < len(content) and content[i] != "\n":
                i += 1
            continue

        current_statement += char

        if char == ".":
            statement = current_statement.strip()
            if statement:
                statement = " ".join(statement.split())
                if statement.startswith(":-"):
                    directive_body = statement[2:].strip()
                    goals = parse_string(directive_body)

                    if (
                        goals
                        and isinstance(goals[0][0], Struct)
                        and (
                            goals[0][0].name == "initialization"
                            or goals[0][0].name == "초기화"
                        )
                    ):
                        if len(goals[0][0].params) != 1:
                            raise ErrUnknownPredicate(
                                "", len(goals[0][0].params)
                            )
                        init_goal = goals[0][0].params[0]
                        pending_goals.append(init_goal)
                    else:
                        success, unifs = solve([], goals, debug_state)
                        print_result(success, unifs)
                else:
                    statements.append(statement)
            current_statement = ""

        i += 1

    if current_statement.strip():
        raise ErrPeriod(f"'{current_statement.strip()}'")

    clauses = []
    for statement in statements:
        validate_clause_syntax(statement)
        try:
            parsed = parse_string(statement)
            clauses.extend(parsed)
        except Exception as e:
            raise ErrSyntax(f"'{statement}': {e}") from e

    return clauses, pending_goals


def execute_pending_initializations(
    program: List[List[Term]],
    pending_goals: List[Term],
    debug_state: DebugState,
):
    for goal in pending_goals:
        try:
            if (
                isinstance(goal, Struct)
                and goal.name == ","
                and goal.arity == 2
            ):
                flattened_goals = flatten_comma_structure(goal)

                # execute all goals as a sequence
                success, unifs = solve(program, flattened_goals, debug_state)
                print_result(success, unifs)
            else:
                # single goal - execute directly
                success, unifs = solve(program, [goal], debug_state)
                print_result(success, unifs)

        except ErrProlog as e:
            handle_error(e, "initialization goal")


def validate_clause_syntax(statement: str) -> None:
    statement = statement.strip()
    if not statement or not statement.endswith("."):
        return

    content = statement[:-1].strip()

    if content.count(":-") > 1:
        raise ErrOperator(statement, True)

    import re

    missing_op_pattern = r"\)\s*(_[가-힣]|[a-zA-Z_])"
    if re.search(missing_op_pattern, content):
        raise ErrOperator(statement, False)


def execute(program: List[List[Term]]) -> None:
    current_file = None
    debug_state = DebugState()
    while True:
        try:
            if debug_state.trace_mode:
                print("[추적]   ", end="")
            command_input = read_multi_line_input()
            validate_clause_syntax(command_input)
        except EOFError:
            break
        except ErrSyntax as e:
            handle_error(e, "input")
            continue

        try:
            cmd = parse_command(command_input)
        except ErrProlog as e:
            handle_error(e, "command parsing")
            continue

        if isinstance(cmd, Load):
            print(f"{cmd.path}에서 적재했습니다")
            try:
                current_file = cmd.path
                program, pending = parse_file_multiline(cmd.path, debug_state)
                execute_pending_initializations(program, pending, debug_state)

            except ErrProlog as e:
                handle_error(e, "parsing")
            except FileNotFoundError:
                handle_error(ErrFileNotFound(cmd.path), "file loading")
        elif isinstance(cmd, Make):
            if current_file:
                try:
                    program, p = parse_file_multiline(current_file, debug_state)
                    print(f"{current_file}에서 재적재했습니다")
                except ErrProlog as e:
                    handle_error(e, "reloading")
                except FileNotFoundError:
                    handle_error(ErrFileNotFound(current_file), "reloading")
            else:
                print("재적재할 파일리 없습니다")
        elif isinstance(cmd, Trace):
            debug_state.trace_mode = True
            print("참.")
        elif isinstance(cmd, NoTrace):
            debug_state.trace_mode = False
            print("참.")
        elif isinstance(cmd, Listing):
            if current_file:
                try:
                    with open(current_file, "r") as f:
                        for line in f:
                            if (cmd.predicate_name == "none") or (
                                cmd.predicate_name in line
                            ):
                                print(line, end="")
                        print("")
                except FileNotFoundError:
                    handle_error(ErrFileNotFound(current_file), "listing")
            else:
                print("목록할 파일이 없읍니다")
        elif isinstance(cmd, Halt):
            break
        elif isinstance(cmd, Query):
            try:
                goals = parse_string(cmd.query)
            except ErrProlog as e:
                handle_error(e, "query")
                continue
            if not goals:
                print("목표가 구문 분석되지 않았습니다")
                continue
            try:
                success, unifs = solve(program, goals[0], debug_state)
                print_result(success, unifs)
            except ErrProlog as e:
                handle_error(e, "solving")
                continue


def print_result(result: bool, unifications: List[dict]) -> None:
    if all(not unif for unif in unifications):
        if result is True:
            print("참")
        else:
            print("거짓")
    else:
        # Print first solution
        if unifications:
            first_unification = unifications[0]
            for key, value in first_unification.items():
                formatted_value = format_term(value)
                print(f"{key} = {formatted_value}", end="")
                if len(first_unification) > 1:
                    print("")

            # If there are more solutions, handle them interactively
            for i in range(1, len(unifications)):
                try:
                    user_input = input()
                    if user_input != ";":
                        return
                    # Print next solution
                    unification = unifications[i]
                    for key, value in unification.items():
                        formatted_value = format_term(value)
                        print(f"{key} = {formatted_value}", end="")
                        if len(first_unification) > 1:
                            print("")
                except EOFError:
                    return
            print("")
