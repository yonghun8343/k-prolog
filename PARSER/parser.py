# coding: utf-8
import re
from typing import Dict, List, Tuple

from UTIL.err import (
    ErrCommandFormat,
    ErrInvalidTerm,
    ErrParenthesis,
    ErrProlog,
    ErrUnexpected,
    ErrUnknownPredicate,
)
from PARSER.ast import Struct, Term, Variable
from PARSER.Data.list import PrologList


def has_top_level_comma(s: str) -> bool:
    depth = 0
    bracket_depth = 0
    inside_if_then_else = False

    i = 0
    while i < len(s):
        ch = s[i]

        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "[":
            bracket_depth += 1
        elif ch == "]":
            bracket_depth -= 1
        elif s[i : i + 2] == "->":
            if depth == 0 and bracket_depth == 0:
                inside_if_then_else = True
            i += 1
        elif (
            ch == ","
            and depth == 0
            and bracket_depth == 0
            and not inside_if_then_else
        ):
            return True
        i += 1
    return False


def has_top_level_operator(s: str, operator: str) -> bool:
    depth = 0
    bracket_depth = 0
    inside_if_then_else = False
    op_len = len(operator)
    i = 0

    while i < len(s):
        ch = s[i]

        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "[":
            bracket_depth += 1
        elif ch == "]":
            bracket_depth -= 1
        elif s[i : i + 2] == "->":
            if depth == 0 and bracket_depth == 0:
                inside_if_then_else = True
            i += 1
        elif (
            s[i : i + op_len] == operator
            and depth == 0
            and bracket_depth == 0
            and not inside_if_then_else
        ):
            return True
        i += 1
    return False


def split_args(s: str) -> List[str]:
    parts, buf, depth, bracket_depth = [], "", 0, 0
    for ch in s:
        if ch == "," and depth == 0 and bracket_depth == 0:
            parts.append(buf.strip())
            buf = ""
        else:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif ch == "[":
                bracket_depth += 1
            elif ch == "]":
                bracket_depth -= 1
            buf += ch
    if buf.strip():
        parts.append(buf.strip())
    return parts


def parse_primary(tokens: List[str], pos: int, operators) -> Tuple[Term, int]:
    if pos >= len(tokens):
        raise ErrUnexpected("")

    token = tokens[pos]

    if token in operators and pos + 1 < len(tokens) and tokens[pos + 1] == "(":
        op_name = token
        pos += 2

        args = []
        while pos < len(tokens) and tokens[pos] != ")":
            if tokens[pos] == ",":
                pos += 1
                continue
            arg, pos = parse_precedence(tokens, pos, 1000, operators)
            args.append(arg)

        if pos >= len(tokens) or tokens[pos] != ")":
            raise ErrParenthesis("closing")

        return Struct(op_name, len(args), args), pos + 1

    if token == "(":
        og_pos = pos + 1
        paren_depth = 0
        search_pos = pos + 1

        while search_pos < len(tokens):
            if tokens[search_pos] == "(":
                paren_depth += 1
            elif tokens[search_pos] == ")":
                if paren_depth == 0:
                    break
                paren_depth -= 1
            search_pos += 1

        if search_pos >= len(tokens):
            raise ErrParenthesis("closing")
        content_tokens = tokens[og_pos:search_pos]
        content_str = ""
        for i, token in enumerate(content_tokens):
            if token in ["(", ")", ","] or (
                i > 0 and content_tokens[i - 1] in ["(", ","]
            ):
                content_str += token
            else:
                if content_str and content_str[-1] not in ["(", ","]:
                    content_str += " "
                content_str += token

        if "," in content_str:
            parts = split_args(content_str)
            goals = [parse_struct(part.strip()) for part in parts]
            if len(goals) == 1:
                return goals[0], search_pos + 1
            else:
                result = goals[0]
                for goal in goals[1:]:
                    result = Struct(",", 2, [result, goal])
                return result, search_pos + 1
        else:
            return parse_struct(content_str), search_pos + 1

    if token in ["+", "-"] and pos + 1 < len(tokens):
        operand, pos = parse_primary(tokens, pos + 1, operators)
        return Struct(token, 1, [operand]), pos

    if re.match(r"^\d+\.?\d*$", token):
        return Struct(token, 0, []), pos + 1

    if token[0].isupper() or token[0] == "_":
        return Variable(token), pos + 1

    else:  # FIXME
        return Struct(token, 0, []), pos + 1

    raise ErrUnexpected(f"{token}")


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

        if (min_prec != 1000) and (operator_prec >= min_prec):
            break

        pos += 1

        next_min_prec = operator_prec - 1 if is_left_assoc else operator_prec

        right, pos = parse_precedence(tokens, pos, next_min_prec, operators)
        left = Struct(operator, 2, [left, right])
    return left, pos


def parse_arithmetic_expression(expr: str) -> Term:
    operators = {
        "*": (400, True),
        "/": (400, True),
        "//": (400, True),
        "나머지": (400, True),
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
        "\=": (700, False),
        "is": (700, False),
        ":=": (700, False),
    }

    expr = expr.strip()

    expr = expr.replace("=\=", "=\\=")

    pattern = r"(=\\=|=:=|>=|=<|//|나머지|mod|is|:=|\d+\.?\d*|[A-Za-z가-힣ㄱ-ㅎㅏ-ㅣ_][A-Za-z가-힣ㄱ-ㅎㅏ-ㅣ0-9_]*|[+\-*/=<>(),])"

    tokens = re.findall(pattern, expr)
    tokenized = [t for t in tokens if t.strip()]

    if not tokenized:
        raise ErrInvalidTerm(expr)

    result, pos = parse_precedence(tokenized, 0, 1000, operators)

    if pos < len(tokens):
        raise ErrUnexpected(f"{tokenized[pos:]}")

    return result


def parse_list(s: str) -> Term:
    s = s.strip()
    content = s[1:-1].strip()

    if not content:  # empty list
        return PrologList().to_struct()

    if "|" in content:  # [H | T] - but need to check if | is at top level
        pipe_pos = find_top_level_pipe(content)
        if pipe_pos != -1:
            head = content[:pipe_pos].strip()
            tail = content[pipe_pos + 1 :].strip()

            if head:
                elements = [
                    parse_term(e.strip()) for e in split_args_smart(head)
                ]
            else:
                elements = []

            tail = parse_term(tail)
            return PrologList(elements, tail).to_struct()

    elements = [parse_term(e.strip()) for e in split_args_smart(content)]
    return PrologList(elements).to_struct()


def find_top_level_pipe(content: str) -> int:
    bracket_depth = 0
    for i, char in enumerate(content):
        if char == "[":
            bracket_depth += 1
        elif char == "]":
            bracket_depth -= 1
        elif char == "|" and bracket_depth == 0:
            return i
    return -1


def split_args_smart(args_str: str) -> List[str]:
    if not args_str.strip():
        return []

    args = []
    current_arg = ""
    bracket_depth = 0
    paren_depth = 0

    for char in args_str:
        if char == "," and bracket_depth == 0 and paren_depth == 0:
            args.append(current_arg.strip())
            current_arg = ""
        else:
            if char == "[":
                bracket_depth += 1
            elif char == "]":
                bracket_depth -= 1
            elif char == "(":
                paren_depth += 1
            elif char == ")":
                paren_depth -= 1
            current_arg += char

    if current_arg.strip():
        args.append(current_arg.strip())

    return args


def parse_struct(s: str) -> Term:
    s = s.strip()
    if s.startswith("(") and s.endswith(")"):
        inner_content = s[1:-1].strip()
        if "," in inner_content and has_top_level_operator(inner_content, ","):
            parts = split_args(inner_content)
            goals = [parse_struct(part.strip()) for part in parts]

            if len(goals) == 1:
                return goals[0]
            else:
                result = goals[0]
                for goal in goals[1:]:
                    result = Struct(",", 2, [result, goal])
                return result
        else:
            return parse_struct(inner_content)
    elif "," in s and has_top_level_comma(s) and "->" not in s:
        parts = split_args(s)
        goals = [parse_struct(part.strip()) for part in parts]
        if len(goals) == 1:
            return goals[0]
        else:
            result = goals[0]
            for goal in goals[1:]:
                result = Struct(",", 2, [result, goal])
            return result
    if "->" in s:
        arrow_pos = s.find("->")
        condition = s[:arrow_pos].strip()

        condition_term = parse_struct(condition)

        action = s[arrow_pos + 2 :].strip()
        if ";" in action:
            actions = action.split(";")
            action_terms = [parse_struct(a.strip()) for a in actions]
            return Struct("->", 3, [condition_term] + action_terms)
        else:
            action_term = parse_struct(action)
            return Struct("->", 2, [condition_term, action_term])

    arithmetic_ops = [
        "+",
        "-",
        "*",
        "/",
        "//",
        "나머지",
        "mod",
        "=:=",
        "=\=",
        ">=",
        "=<",
        ">",
        "<",
        "is",
        ":=",
    ]
    for op in arithmetic_ops:
        op_pattern = re.escape(op) + r"\s*\("
        if re.match(op_pattern, s):
            try:
                return parse_arithmetic_expression(s)
            except ErrProlog:
                # If arithmetic parsing fails, continue with normal struct parsing
                break
    m = re.match(r"^([a-z0-9가-힣][a-zA-Z0-9가-힣_]*)\s*\((.*)\)$", s)
    if (
        s.startswith("\=")
        or "\=" in s
        and "=\=" not in s
        and has_top_level_operator(s, "\=")
    ):
        equals_pos = s.find("\=")
        if equals_pos > 0 and equals_pos < len(s) - 2:
            left_part = s[:equals_pos].strip()
            right_part = s[equals_pos + 2 :].strip()

            left_term = parse_term(left_part)
            right_term = parse_term(right_part)

            return Struct("\\=", 2, [left_term, right_term])
    elif (
        "=" in s
        and "=:=" not in s
        and "=\=" not in s
        and "=<" not in s
        and ">=" not in s
        and ":=" not in s
    ) and has_top_level_operator(s, "="):
        equals_pos = s.find("=")

        if equals_pos > 0 and equals_pos < len(s) - 1:
            left_part = s[:equals_pos].strip()
            right_part = s[equals_pos + 1 :].strip()

            left_term = parse_term(left_part)
            right_term = parse_term(right_part)

            return Struct("=", 2, [left_term, right_term])
        if len(s) == 1 and equals_pos == 0:
            return Struct("=", 0, [])
    elif s.startswith("[") and s.endswith("]"):
        return parse_list(s)
    elif m:
        name = m.group(1)
        args_str = m.group(2)

        # Special handling for findall
        if (
            name == "findall"
            or name == "모두찾기"
            or name == "setof"
            or name == "집합"
        ):
            parts = split_args(args_str)
            if len(parts) != 3:
                raise ErrUnknownPredicate(name, len(parts))

            template = parse_term(parts[0])
            result_bag = parse_term(parts[2])
            query_str = parts[1].strip()
            query_str = parse_struct(query_str)

            if name == "findall" or name == "모두찾기":
                return Struct("findall", 3, [template, query_str, result_bag])
            else:
                return Struct("setof", 3, [template, query_str, result_bag])
        elif name == "forall" or name == "모두만족":
            parts = split_args(args_str)
            if len(parts) != 2:
                raise ErrUnknownPredicate(name, len(parts))

            generator = parse_struct(parts[0].strip())
            test = parse_struct(parts[1].strip())

            return Struct("forall", 2, [generator, test])
        elif name == "maplist" or name == "목록에적용":
            parts = split_args(args_str)
            if len(parts) not in {2, 3, 4, 5}:
                raise ErrUnknownPredicate(name, len(parts))

            predicate = parse_struct(parts[0].strip())
            lists = [parse_struct(p.strip()) for p in parts[1:]]

            return Struct("maplist", len(parts), [predicate] + lists)

        elif (
            name == "writeln"
            or name == "write"
            or name == "쓰기"
            or name == "쓰고줄바꿈"
        ):
            if args_str.startswith('"') and args_str.endswith('"'):
                return Struct(name, 1, [args_str])
            else:
                parts = split_args(args_str)
                params = [parse_term(p) for p in parts]
                return Struct(name, len(params), params)
        else:
            parts = split_args(args_str)
            params = [parse_term(p) for p in parts]
            return Struct(name, len(params), params)
    else:
        if not s:
            raise ErrInvalidTerm("빈 항")
        if any(op in s for op in arithmetic_ops):
            try:
                result = parse_arithmetic_expression(s)
                return result
            except (ErrProlog, Exception) as e:
                for op in ["-", "+", "*", "/"]:
                    if op in s:
                        paren_depth = 0
                        op_pos = -1
                        for i, char in enumerate(s):
                            if char == "(":
                                paren_depth += 1
                            elif char == ")":
                                paren_depth -= 1
                            elif char == op and paren_depth == 0:
                                op_pos = i
                                break

                        if op_pos > 0:
                            left_part = s[:op_pos].strip()
                            right_part = s[op_pos + 1 :].strip()

                            try:
                                left_term = (
                                    parse_term(left_part) if left_part else None
                                )
                                right_term = (
                                    parse_term(right_part)
                                    if right_part
                                    else None
                                )

                                if left_term and right_term:
                                    result = Struct(
                                        op, 2, [left_term, right_term]
                                    )
                                    return result
                            except Exception as e:
                                continue
                pass

        if s[0].isupper() or s[0] == "_":
            return Variable(s)
        else:
            result = Struct(s, 0, [])
            return result


def parse_term(s: str) -> Term:
    s = s.strip()

    if any(
        op in s
        for op in [
            "is",
            ":=",
            "+",
            "-",
            "*",
            "/",
            "//",
            "나머지",
            "mod",
            ">",
            "<",
            ">=",
            "=<",
            "=:=",
            "=\=",
        ]
    ):
        return parse_struct(s)
    if s and (s[0].isupper() or s[0] == "_"):
        if s == "_":
            return Variable(f"_G{generate_unique_id()}")
        return Variable(s)

    return parse_struct(s)


def generate_unique_id() -> int:
    if not hasattr(generate_unique_id, "counter"):
        generate_unique_id.counter = 0
    generate_unique_id.counter += 1
    return generate_unique_id.counter


def flatten_semicolons(head: Term, tail_str: str) -> List[List[Term]]:
    predicates = []
    tails = [parse_struct(part.strip()) for part in tail_str.strip().split(";")]
    if head is not None:
        for tail in tails:
            predicates.append([head] + [tail])
    else:
        for tail in tails:
            predicates.append([tail])

    return predicates


def parse_line(line: str) -> List[Term]:
    stripped = line.strip()
    if not stripped:
        return []
    if not stripped.endswith("."):
        raise ErrCommandFormat(f"{line}은 마침표로 끝나야 합니다")
    body = stripped[:-1]
    if ":-" in body:
        head_str, tail_str = body.split(":-", 1)
        head = parse_struct(head_str.strip())

        if (";" in tail_str) and ("->" not in tail_str):
            return flatten_semicolons(head, tail_str)
        else:
            parts = split_args(tail_str)
            tails = [parse_struct(part.strip()) for part in parts]
            return [head] + tails
    else:
        if (";" in body) and ("->" not in body):
            return flatten_semicolons(None, body)
        else:
            parts = split_args(body)
            structs = [parse_struct(part.strip()) for part in parts]
            return structs


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
