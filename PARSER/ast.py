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

    def __lt__(self, other):
        return (self.name, len(self.params), self.params) < (
            other.name,
            len(other.params),
            other.params,
        )
