#coding: utf-8
import sys
from typing import Optional

IsVerbose = False


def eprint(*args, **kwargs) -> None:
    print(*args, file=sys.stderr, **kwargs)


def handle_error(error: Exception, context: str = "") -> None:
    if IsVerbose:
        eprint(f"문맥맥: {context}")
        eprint(f"오류 타입입: {type(error).__name__}")
    eprint(f"오류: {error}")


class ErrProlog(Exception):
    pass


class ErrSyntax(ErrProlog):
    def __init__(
        self,
        message: str = "",
        line: Optional[int] = None,
        pos: Optional[int] = None,
    ):
        self.message = message
        self.line = line
        self.pos = pos

    def __str__(self) -> str:
        base = "구문 오류"
        if self.line is not None:
            base += f" (라인 {self.line}"
            if self.pos is not None:
                base += f", 위치 {self.pos}"
            base += ")"
        if self.message:
            base += f": {self.message}"
        return base


class ErrPeriod(ErrSyntax):
    def __init__(self, string: str):
        self.string = string

    def __str__(self) -> str:
        if self.string == "":
            return "입력에 마침표가 없읍니다."
        return f"문장 {self.string}에 마침표가 없읍니다"


class ErrOperator(ErrSyntax):
    def __init__(self, statement: str, multiple: bool):
        self.statement = statement
        self.multiple = multiple

    def __str__(self) -> str:
        if self.multiple:
            return f"'{self.statement}'에 연산자가 너무 많습니다"
        return f"'{self.statement}'에 연산자가 필요합니다"


class ErrUnexpected(ErrSyntax):
    def __init__(self, token: str):
        self.token = token

    def __str__(self) -> str:
        return f"예상치 못한 토큰: {self.token}"


class ErrParenthesis(ErrSyntax):
    def __init__(self, missing_type: str = "closing"):
        self.missing_type = missing_type

    def __str__(self) -> str:
        if self.missing_type == "closing":
            return "닫는 괄호가 없읍니다"
        else:
            return "여는 괄호가 없읍니다"


class ErrList(ErrSyntax):
    def __init__(self, err: str = ""):
        self.err = err

    def __str__(self) -> str:
        return f"리스트 오류: {self.err}"


class ErrInvalidTerm(ErrSyntax):
    def __init__(self, term: str):
        self.term = term

    def __str__(self) -> str:
        return f"잘못된 항: {self.term}"


class ErrExecution(ErrProlog):
    pass


class ErrParsing(ErrExecution):
    def __init__(self, parseStr: str):
        self.parseStr = parseStr

    def __str__(self) -> str:
        return f"파싱 오류: {self.parseStr}을 구문 분석할 수 없읍니다"


class ErrUninstantiated(ErrExecution):
    def __init__(self, variable: str = "", context: str = ""):
        self.variable = variable
        self.context = context

    def __str__(self) -> str:
        base = "인수가 충분히 인스턴스화되지 않았습니다"
        if self.variable:
            base += f" (변수: {self.variable})"
        
        return base


class ErrArithmetic(ErrExecution):
    def __init__(self, operation: str, reason: str = ""):
        self.operation = operation
        self.reason = reason

    def __str__(self) -> str:
        base = f"산술 오류: {self.operation}"
        if self.reason:
            base += f" - {self.reason}"
        return base


class ErrDivisionByZero(ErrArithmetic):
    def __init__(self):
        super().__init__("0으로 나누기")


class ErrNotNumber(ErrArithmetic):
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return f"{self.value}은(는) 숫자가 아닙니다"


class ErrUnknownOperator(ErrArithmetic):
    def __init__(self, operator: str):
        self.operator = operator

    def __str__(self) -> str:
        return f"알 수 없는 연산자: {self.operator}"


class ErrDatabase(ErrProlog):
    pass


class ErrUnknownPredicate(ErrDatabase):
    def __init__(self, predicate: str, arity: int):
        self.predicate = predicate
        self.arity = arity

    def __str__(self) -> str:
        return f"알 수 없는 함수: {self.predicate}/{self.arity}"


class ErrFileNotFound(ErrDatabase):
    def __init__(self, filename: str):
        self.filename = filename

    def __str__(self) -> str:
        return f"파일 '{self.filename}' 을(를) 찾을 수 없습니다"


class ErrUnification(ErrExecution):
    def __init__(self, term1: str, term2: str, reason: str = ""):
        self.term1 = term1
        self.term2 = term2
        self.reason = reason

    def __str__(self) -> str:
        base = f"통합 오류: '{self.term1}' 을(를) '{self.term2}'랑 통합 할 수 없습니다"
        if self.reason:
            base += f" - {self.reason}"
        return base


class ErrREPL(ErrProlog):
    pass


class ErrInvalidCommand(ErrREPL):
    def __init__(self, command: str):
        self.command = command

    def __str__(self) -> str:
        return f"잘못된 명령: {self.command}"


class ErrCommandFormat(ErrREPL):
    def __init__(self, command: str, expected_format: str):
        self.command = command
        self.expected_format = expected_format

    def __str__(self) -> str:
        return f"명령 형식 오류: {self.command} (예상 형식: {self.expected_format})"
