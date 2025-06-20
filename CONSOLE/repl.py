from typing import List

from PARSER.ast import Term
from PARSER.parser import parse_file, parse_string
from SOLVER.solver import solve


class Command:
    pass


class Load(Command):
    def __init__(self, path: str):
        if "." not in path:
            path += ".txt" #TODO hardcoded right now
        self.path = path


class Make(Command):
    pass


class Query(Command):
    def __init__(self, query: str):
        self.query = query


class Halt(Command):
    pass


def parse_command(command: str) -> Command:
    if command.startswith("[") and command.endswith("]."):
        return Load(command[1:-2]) # range is hard coded right now
    elif command == "make.":
        return Make()
    elif command.startswith("halt."):
        return Halt()
    else:
        return Query(command)


def execute(program: List[List[Term]]) -> None:
    current_file = None
    while True:
        try:
            line = input("?- ")
        except EOFError:
            break
        cmd = parse_command(line)
        if isinstance(cmd, Load):
            print(f"loaded from {cmd.path}")
            try:
                current_file = cmd.path
                program = parse_file(cmd.path)
            except Exception as e:
                print(e)
        elif isinstance(cmd, Make):
                if current_file:
                    try:
                        program = parse_file(current_file)
                        print(f"reloaded from {current_file}")
                    except Exception as e:
                        print(e)
                else:
                    print("No file to reload")
            
        elif isinstance(cmd, Halt):
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
