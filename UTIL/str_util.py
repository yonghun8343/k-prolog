from typing import List

from PARSER.ast import Struct, Term, Variable


def flatten_comma_structure(term: Term) -> List[Term]:
    if isinstance(term, Struct) and term.name == "," and term.arity == 2:
        left_goals = flatten_comma_structure(term.params[0])
        right_goals = flatten_comma_structure(term.params[1])
        return left_goals + right_goals
    else:
        return [term]

def term_to_string(term: Term) -> str:
    if isinstance(term, Variable):
        return term.name
    elif isinstance(term, Struct):
        if term.arity == 0:
            return term.name
        elif term.name == ":-" and term.arity == 2:
            # Rule: head :- body
            head = term_to_string(term.params[0])
            body = term_to_string(term.params[1])
            return f"{head} :- {body}"
        elif term.name == "," and term.arity == 2:
            # Don't start with comma - just join the parts
            left = term_to_string(term.params[0])
            right = term_to_string(term.params[1])
            return f"{left}, {right}"  # No leading comma!
        elif term.name == ";" and term.arity == 2:
            left = term_to_string(term.params[0])
            right = term_to_string(term.params[1])
            return f"{left}; {right}"
        else:
            params_str = ", ".join(term_to_string(p) for p in term.params)
            return f"{term.name}({params_str})"
    else:
        return str(term)


def format_term(term: Term) -> str:
    if isinstance(term, Struct):
        if isinstance(term, Struct) and (term.name == "[]" or term.name == "."):
            return format_list(term)
        else:
            if term.arity == 0:
                return term.name
            else:
                binary_operators = [
                    "+", "-", "*", "/", "//", "mod", "=:=", "=\\=", 
                    "<", ">", ">=", "=<", "=", "is", ":="
                ]
                if term.name in binary_operators and term.arity == 2:
                    left = format_term(term.params[0])
                    right = format_term(term.params[1])
                    return f"{left}{term.name}{right}"
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


def struct_to_infix(term: Term) -> str:
    if not isinstance(term, Struct):
        if isinstance(term, Variable):
            return term.name
        else:
            return str(term)

    binary_operators = [
        "+",
        "-",
        "*",
        "/",
        "//",
        "mod",
        "=:=",
        "=\\=",
        "<",
        ">",
        ">=",
        "=<",
        "=",
        "is",
        ":=",
    ]

    if term.arity > 0:
        param_strs = [struct_to_infix(param) for param in term.params]
    else:
        param_strs = []

    # If it's a binary operator, convert to infix
    if term.name in binary_operators and term.arity == 2:
        return f"{param_strs[0]} {term.name} {param_strs[1]}"

    elif term.name in ["+", "-"] and term.arity == 1:
        return f"{term.name}{param_strs[0]}"

    elif term.name == "." and term.arity == 2:
        return dot_to_list_notation(term)
    elif term.name == "[]" and term.arity == 0:
        return "[]"

    else:
        if term.arity == 0:
            return term.name
        else:
            return f"{term.name}({','.join(param_strs)})"


def dot_to_list_notation(term: Term) -> str:
    if not isinstance(term, Struct):
        return str(term)

    if term.name == "." and term.arity == 2:
        elements = []
        current = term

        while (
            isinstance(current, Struct)
            and current.name == "."
            and current.arity == 2
        ):
            elements.append(current.params[0])
            current = current.params[1]

        if (
            isinstance(current, Struct)
            and current.name == "[]"
            and current.arity == 0
        ):
            element_strs = [dot_to_list_notation(elem) for elem in elements]
            return "[" + ",".join(element_strs) + "]"
        else:
            element_strs = [dot_to_list_notation(elem) for elem in elements]
            tail_str = dot_to_list_notation(current)
            if elements:
                return "[" + ",".join(element_strs) + "|" + tail_str + "]"
            else:
                return tail_str

    elif term.name == "[]" and term.arity == 0:
        return "[]"

    else:
        if term.arity == 0:
            return term.name
        else:
            param_strs = [dot_to_list_notation(param) for param in term.params]
            return f"{term.name}({','.join(param_strs)})"
