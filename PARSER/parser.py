import re
from typing import List, Tuple, Dict

from PARSER.ast import Struct, Term, Variable


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


def parse_primary(tokens: List[str], pos: int, operators) -> Tuple[Term, int]:
    if pos >= len(tokens):
        raise ValueError("Unexpected end of expression")

    token = tokens[pos]

    if token == "(":
        expr, pos = parse_precedence(tokens, pos + 1, 1000, operators)
        if pos >= len(tokens) or tokens[pos] != ")":
            raise ValueError("Missing closing parenthesis")
        return expr, pos + 1

    if token in ["+", "-"] and pos + 1 < len(tokens):
        operand, pos = parse_primary(tokens, pos + 1, operators)
        return Struct(token, 1, [operand]), pos

    if re.match(r"^\d+\.?\d*$", token):
        return Struct(token, 0, []), pos + 1

    if re.match(r"^[A-Z_]", token):
        return Variable(token), pos + 1

    if re.match(r"^[a-z]", token):
        return Struct(token, 0, []), pos + 1

    raise ValueError(f"Unexpected token: {token}")


def parse_precedence(
    tokens: List[str],
    pos: int,
    min_prec: int,
    operators: Dict[str, Tuple[int, bool]],
) -> Tuple[Term, int]:
    left, pos = parse_primary(tokens, pos, operators)
    while pos < len(tokens):
        operator = tokens[pos]
        if operator not in operators:
            break

        operator_prec, is_left_assoc = operators[operator]

        if (min_prec != 1000) and (
            operator_prec >= min_prec
        ): 
            break

        pos += 1

        next_min_prec = operator_prec - 1 if is_left_assoc else operator_prec

        right, pos = parse_precedence(tokens, pos, next_min_prec, operators)
        left = Struct(operator, 2, [left, right])
    return left, pos


def parse_arithmetic_expression(expr: str) -> Term:
    operators = {  # this ds might need to become flexible
        "*": (400, True),  # True is left, False is right
        "/": (400, True),
        "//": (400, True),
        "mod": (400, True),
        "+": (500, True),
        "-": (500, True),
        "=:=": (700, False),
        "=\=": (700, False),
        "<": (700, False),
        ">": (700, False),
        ">=": (700, False),
        "=<": (700, False),
        "=": (700, False),
        "is": (700, False),
    }

    expr = expr.strip()
    pattern = r"(=:=|=\\=|>=|=<|//|mod|is|\d+\.?\d*|[A-Za-z_][A-Za-z0-9_]*|[+\-*/=<>()])"
    tokens = re.findall(pattern, expr)
    tokenized = [t for t in tokens if t.strip()]
    if not tokenized:
        raise ValueError("Empty Expression")

    result, pos = parse_precedence(tokens, 0, 1000, operators)

    if pos < len(tokens):
        raise ValueError(f"Unexpected tokens: {tokens[pos:]}")

    return result


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
        if any(
            op in s
            for op in [
                "is",
                "+",
                "-",
                "*",
                "/",
                "//",
                "mod",
                ">",
                "<",
                ">=",
                "=<",
                "=:=",
                "=\=",
            ]
        ):
            try:
                result = parse_arithmetic_expression(s)
                return result
            except ValueError as e:
                print(f"failed to parse {s}: {e}")

        elif s[0].isupper() or s[0] == "_":
            return Variable(s)  # TODO need variable checking
        return Struct(s, 0, [])


def parse_term(s: str) -> Term:
    s = s.strip()
    if s and (s[0].isupper() or s[0] == "_"):
        return Variable(s)
    return parse_struct(s)


def flatten_semicolons(head: Term, tail_str: str) -> List[List[Term]]:
    predicates = []
    tails = [parse_struct(part.strip()) for part in tail_str.strip().split(";")]
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

        if ";" in tail_str:
            return flatten_semicolons(head, tail_str)
        else:
            parts = split_args(tail_str)
            tails = [parse_struct(part.strip()) for part in parts]
            return [head] + tails
    else:
        return [parse_struct(body)]


def parse_string(s: str) -> List[List[Term]]:
    parsed = []
    for line in s.splitlines():
        parsed_line = parse_line(line)
        if (
            parsed_line
            and isinstance(parsed_line, list)
            and isinstance(parsed_line[0], list)
        ):  
            for p in parsed_line:
                parsed.append(p)
        else:
            parsed.append(parsed_line)
    return parsed


def parse_file(path: str) -> List[List[Term]]:
    with open(path, "r") as f:
        return parse_string(f.read())
