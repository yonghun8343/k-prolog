import re, itertools
from typing import List
from PARSER.ast import Term, Variable, Struct

def split_args(s: str) -> List[str]:
    parts, buf, depth = [], "", 0
    for ch in s:
        if ch == "," and depth == 0:
            parts.append(buf)
            buf = ""
        else:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            buf += ch
    if buf:
        parts.append(buf)
    return parts


def parse_struct(s: str) -> Term:
    s = s.strip()
    m = re.match(r"^([a-z0-9][a-zA-Z0-9_]*)\s*\((.*)\)$", s)
    if m:
        name = m.group(1)
        args_str = m.group(2)
        parts = split_args(args_str)
        params = [parse_term(p) for p in parts]
        return Struct(name, len(params), params)
    else:
        if not s:
            raise ValueError("Empty term")
        if "is" in s:
            name = "is"
            params = s.split("is")
            return Struct(name, 2, params)
        elif s[0].isupper() or s[0] == "_":
            return Variable(s) #TODO need variable checking
        print("reached here")
        return Struct(s, 0, [])


def parse_term(s: str) -> Term:
    s = s.strip()
    if s and (s[0].isupper() or s[0] == "_"):
        return Variable(s)
    return parse_struct(s)

def flatten_semicolons(head: Term, tail_str: str) -> List[List[Term]]:
    predicates = [] 
    tails = [parse_struct(part.strip()) for part in tail_str.strip().split(';')]
    for tail in tails:
        predicates.append([head] + [tail])
    return predicates


def parse_line(line: str) -> List[Term]:
    stripped = line.strip()
    if not stripped:
        return []
    if not stripped.endswith("."):
        raise ValueError(f"Line must end with '.': {line}")
    body = stripped[:-1]
    if ":-" in body:
        head_str, tail_str = body.split(":-", 1)
        
        head = parse_struct(head_str.strip())

        if ';' in tail_str:
            return flatten_semicolons(head, tail_str)
        else:
            # split_args 로 최상위 쉼표만 분리
            parts = split_args(tail_str)
            tails = [parse_struct(part.strip()) for part in parts]
            return [head] + tails
    else:
        return [parse_struct(body)]


def parse_string(s: str) -> List[List[Term]]:
    parsed = []
    for l in s.splitlines():
        parsed_line = parse_line(l)
        if parsed_line and isinstance(parsed_line, list) and isinstance(parsed_line[0], list): # check nested:
            for p in parsed_line:
                parsed.append(p)
        else:
            parsed.append(parsed_line)
    return parsed


def parse_file(path: str) -> List[List[Term]]:
    with open(path, "r") as f:
        return parse_string(f.read())

