import re
from typing import List


class Term:
    pass


class Variable(Term):
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, Variable) and self.name == other.name

    def __hash__(self):
        return hash(self.name)


class Struct(Term):
    def __init__(self, name: str, arity: int, params: List[Term]):
        self.name = name
        self.arity = arity
        self.params = params

    def __repr__(self):
        if self.arity == 0:
            return self.name
        return f"{self.name}(" + ",".join(map(str, self.params)) + ")"

    def __eq__(self, other):
        return (
            isinstance(other, Struct)
            and self.name == other.name
            and self.arity == other.arity
            and self.params == other.params
        )

    def __hash__(self):
        return hash((self.name, self.arity, tuple(self.params)))


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
        if s[0].isupper() or s[0] == "_":
            return Variable(s)
        return Struct(s, 0, [])


def parse_term(s: str) -> Term:
    s = s.strip()
    if s and (s[0].isupper() or s[0] == "_"):
        return Variable(s)
    return parse_struct(s)


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
        # split_args 로 최상위 쉼표만 분리
        parts = split_args(tail_str)
        tails = [parse_struct(part.strip()) for part in parts]
        return [head] + tails
    else:
        return [parse_struct(body)]


def parse_string(s: str) -> List[List[Term]]:
    return [parse_line(l) for l in s.splitlines()]


def parse_file(path: str) -> List[List[Term]]:
    with open(path, "r") as f:
        return parse_string(f.read())
