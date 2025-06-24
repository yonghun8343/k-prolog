from typing import List

from PARSER.ast import Term
from PARSER.parser import parse_file, parse_string
from SOLVER.solver import solve

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
            raise ValueError(f"Unknown procedure: {command}")
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
                print("program", program)
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
        elif isinstance(cmd, Listing):
            if current_file:
                with open(current_file, "r") as f:
                    for line in f:
                        if (cmd.predicate_name == "none") or (
                            cmd.predicate_name in line
                        ):
                            print(line, end="")
                    print("")
            else:
                print("No file to list")
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
            try:
                success, unifs = solve(program, goals[0])
                print_result(success, unifs)
            except ValueError as e:
                print(f"ERROR: {e}")
                continue


def print_result(result: bool, unifications: List[dict]) -> None:
    if all(not unif for unif in unifications):
        print(result)
    else:
        for unification in unifications:
            for key, value in unification.items():
                print(f"{key} = {value}", end=" ")
            
