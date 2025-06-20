from typing import List

from PARSER.ast import Term
from PARSER.parser import parse_file, parse_string
from SOLVER.solver import solve


class Command:
    pass


class Load(Command):
    def __init__(self, path: str):
        self.path = path


class Append(Command):
    def __init__(self, path: str):
        self.path = path


class Query(Command):
    def __init__(self, query: str):
        self.query = query


class Quit(Command):
    pass


def parse_command(command: str) -> Command:
    if command.startswith(":l "):
        return Load(command[3:])
    elif command.startswith(":a "):
        return Append(command[3:])
    elif command.startswith(":q"):
        return Quit()
    else:
        return Query(command)


def execute(program: List[List[Term]]) -> None:
    while True:
        try:
            line = input("?- ")
        except EOFError:
            break
        cmd = parse_command(line)
        if isinstance(cmd, Load):
            print(f"loaded from {cmd.path}")
            try:
                program = parse_file(cmd.path)
            except Exception as e:
                print(e)
        elif isinstance(cmd, Append):
            try:
                more = parse_file(cmd.path)
                program = more + program
            except Exception as e:
                print(e)
        elif isinstance(cmd, Quit):
            break
        elif isinstance(cmd, Query):
            try:
                goals = parse_string(cmd.query)
            except Exception as e:
                print(e)
                continue
            if not goals:
                print("No goals parsed.")
                continue
            success, unifs = solve(program, goals[0])
            print_result(success, unifs)


def print_result(result: bool, unifications: List[dict]) -> None:
    print(result)
    for unification in unifications:
        for key, value in unification.items():
            print(f"{key} = {value}", end=" ")
            if input() == ";":
                continue


def main() -> None:
    execute([])


if __name__ == "__main__":
    main()
