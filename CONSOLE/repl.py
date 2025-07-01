from typing import List

from PARSER.ast import Term, Struct, Variable
from PARSER.parser import parse_file, parse_string
from SOLVER.solver import solve

from err import *


class Command:
    pass


class Load(Command):
    def __init__(self, path: str):
        if "." not in path:
            path += ".txt"  # TODO hardcoded right now
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

        except EOFError:
            if lines:
                raise ErrSyntax("Incomplete input - missing period")
            else:
                raise EOFError

    full_input = " ".join(line.strip() for line in lines)
    return full_input


def parse_command(command: str) -> Command:
    if command.startswith("[") and command.endswith("]."):
        return Load(command[1:-2])
    elif command.startswith("consult(") and command.endswith(")."):
        return Load(command[8:-2])
    elif command == "make.":
        return Make()
    elif command == "halt.":
        return Halt()
    elif command.startswith("listing"):
        if command == "listing.":
            return Listing("none")
        elif command.startswith("listing(") and command.endswith(")."):
            return Listing(command[8:-2])
        else:
            raise ErrInvalidCommand(command)
    else:
        return Query(command)


def parse_file_multiline(filepath: str) -> List[List[Term]]:
    with open(filepath, "r") as f:
        content = f.read()

    statements = []
    current_statement = ""

    i = 0
    while i < len(content):
        char = content[i]
        current_statement += char

        if char == ".":
            statement = current_statement.strip()
            if statement:
                statement = " ".join(statement.split())
                statements.append(statement)
            current_statement = ""

        i += 1

    if current_statement.strip():
        raise ErrSyntax(f"Incomplete statement: {current_statement.strip()}")

    clauses = []
    for statement in statements:
        try:
            parsed = parse_string(statement)
            clauses.extend(parsed)
        except Exception as e:
            raise ErrSyntax(f"Error parsing statement '{statement}': {e}")

    return clauses


def execute(program: List[List[Term]]) -> None:
    current_file = None
    while True:
        try:
            command_input = read_multi_line_input()
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
            print(f"loaded from {cmd.path}")
            try:
                current_file = cmd.path
                program = parse_file_multiline(cmd.path)
            except ErrProlog as e:
                handle_error(e, "parsing")
            except FileNotFoundError:
                handle_error(ErrFileNotFound(cmd.path), "file loading")
        elif isinstance(cmd, Make):
            if current_file:
                try:
                    program = parse_file_multiline(current_file)
                    print(f"reloaded from {current_file}")
                except ErrProlog as e:
                    handle_error(e, "reloading")
                except FileNotFoundError:
                    handle_error(ErrFileNotFound(current_file), "reloading")
            else:
                print("No file to reload")
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
                print("No file to list")
        elif isinstance(cmd, Halt):
            break
        elif isinstance(cmd, Query):
            try:
                goals = parse_string(cmd.query)
            except ErrProlog as e:
                handle_error(e, "query")
                continue
            if not goals:
                print("No goals parsed.")
                continue
            try:
                success, unifs = solve(program, goals[0])
                print_result(success, unifs)
            except ErrProlog as e:
                handle_error(e, "solving")
                continue


def print_result(result: bool, unifications: List[dict]) -> None:
    if all(not unif for unif in unifications):
        print(result)
    else:
        for unification in unifications:
            for key, value in unification.items():
                formatted_value = format_term(value)
                print(f"{key} = {formatted_value}")


def format_term(term: Term) -> str:
    if isinstance(term, Struct):
        if isinstance(term, Struct) and (term.name == "[]" or term.name == "."):
            return format_list(term)
        else:
            if term.arity == 0:
                return term.name
            else:
                params = ", ".join(format_term(p) for p in term.params)
                return f"{term.name}({params})"
    elif isinstance(term, Variable):
        return term.name
    else:
        return str(term)


def format_list(term: Term, elements: List[str] = None) -> str:
    if elements is None:
        elements = []

    if isinstance(term, Struct):
        if term.name == "[]" and term.arity == 0:
            return "[" + ", ".join(elements) + "]"
        elif term.name == "." and term.arity == 2:
            head, tail = term.params
            elements.append(format_term(head))
            return format_list(tail, elements)
        else:
            tail_str = format_term(term)
            return "[" + ", ".join(elements) + "|" + tail_str + "]"
    else:
        tail_str = format_term(term)
        return "[" + ", ".join(elements) + "|" + tail_str + "]"
