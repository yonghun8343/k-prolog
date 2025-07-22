import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import subprocess
import tempfile
import unittest

from err import (
    ErrDivisionByZero,
    ErrFileNotFound,
    ErrInvalidCommand,
    ErrNotNumber,
    ErrOperator,
    ErrParenthesis,
    ErrParsing,
    ErrPeriod,
    ErrUnexpected,
    ErrUninstantiated,
    ErrUnknownPredicate,
)


class TestKProlog(unittest.TestCase):
    def setUp(self):
        self.interpreter_path = "/usr/bin/python3"
        self.main_script = "/Users/yuminlee/k-prolog/main.py"
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        for file in os.listdir(self.test_dir):
            os.remove(os.path.join(self.test_dir, file))
        os.rmdir(self.test_dir)

    def create_test_file(self, filename, content):
        filepath = os.path.join(self.test_dir, filename)
        with open(filepath, "w") as f:
            f.write(content)
        return filepath

    def run_prolog_commands(self, commands, timeout=10):
        process = subprocess.Popen(
            [self.interpreter_path, self.main_script],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=self.test_dir,
        )

        # send commands
        input_text = "\n".join(commands) + "\n종료.\n"
        try:
            stdout, stderr = process.communicate(
                input=input_text, timeout=timeout
            )
            return stdout, stderr, process.returncode
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            return stdout, stderr, -1

    def test_file_loading_and_facts(self):
        content = """부모(john, mary).
                    부모(john, tom).
                    부모(sue, mary).
                    부모(sue, tom).
                    좋아함(mary, pizza).
                    좋아함(john, pasta)."""

        self.create_test_file("사실.pl", content)

        commands = [
            "[사실].",
            "부모(john, mary).",  # Should succeed
            "부모(mary, john).",  # Should fail
            "부모(john, _X).",
            ";",
            ";",  # Should give multiple solutions (mary, tom)
            "좋아함(mary, pizza).",  # Should succeed
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("사실.pl에서 적재했습니다", stdout)
        self.assertIn("참", stdout)
        self.assertIn("거짓", stdout)
        self.assertIn("_X = mary", stdout)
        self.assertIn("_X = tom", stdout)
        self.assertIn("참", stdout)

    def test_recursive_factorial(self):
        content = """팩토리얼(0, 1).
                    팩토리얼(_N, _결과) :- _N > 0, _N1 := _N - 1, 팩토리얼(_N1, _서브결과), _결과 := _N * _서브결과."""

        self.create_test_file("팩토리얼.pl", content)

        commands = [
            "[팩토리얼].",
            "팩토리얼(5, _X).",  # Should give X = 120
            "팩토리얼(0, _Y).",  # Should give Y = 1
            "팩토리얼(3, _Z).",  # Should give Z = 6
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("팩토리얼.pl에서 적재했습니다", stdout)
        self.assertIn("_X = 120", stdout)
        self.assertIn("_Y = 1", stdout)
        self.assertIn("_Z = 6", stdout)

    def test_recursive_sum(self):
        content = """합집(0, 0).
                    합집(_N, _결과) :- _N > 0, _N1 := _N - 1, 합집(_N1, _서브결과), _결과 := _N + _서브결과."""

        self.create_test_file("합집.pl", content)

        commands = [
            "[합집].",
            "합집(5, _X).",  # Should give X = 15 (0+1+2+3+4+5)
            "합집(3, _Y).",  # Should give Y = 6 (0+1+2+3)
            "합집(0, _Z).",  # Should give Z = 0
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("합집.pl에서 적재했습니다", stdout)
        self.assertIn("_X = 15", stdout)
        self.assertIn("_Y = 6", stdout)
        self.assertIn("_Z = 0", stdout)

    def test_conjunction_comma(self):
        content = """부모(존, 매리).
                     부모(매리, 쑤).
                     여자(매리).
                     여자(쑤).
                     엄마(_X) :- 부모(_아무, _X), 여자(_X).
                     """

        self.create_test_file("논리곱.pl", content)

        commands = [
            "[논리곱].",
            "엄마(_X).",
            ";",
            ";",  # Should give multiple solutions, X = mary, sue
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("논리곱.pl에서 적재했습니다", stdout)
        self.assertIn("_X = 매리", stdout)
        self.assertIn("_X = 쑤", stdout)

    def test_disjunction_semicolon(self):
        content = """언어(prolog).
                     언어(c).
                     강의(prolog).
                     강의(python).
                     흥미로운(_X) :- 언어(_X); 강의(_X)."""

        self.create_test_file("논리합.pl", content)

        commands = [
            "[논리합].",
            "흥미로운(_X).",
            ";",
            ";",
            ";",
        ]  # Should give multiple solutions, X = prolog, c, python

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("논리합.pl에서 적재했습니다", stdout)
        self.assertIn("_X = prolog", stdout)
        self.assertIn("_X = c", stdout)
        self.assertIn("_X = python", stdout)

    def test_make_reload(self):
        # Create initial file
        content1 = "테스트_사실(원본)."
        filepath = self.create_test_file("재적재_테스트.pl", content1)

        commands = [
            "[재적재_테스트].",
            "테스트_사실(_X).",  # Should get original
        ]

        stdout1, stderr1, returncode1 = self.run_prolog_commands(commands)

        # Modify the file
        content2 = "테스트_사실(새로운)."
        with open(filepath, "w") as f:
            f.write(content2)

        commands2 = [
            "[재적재_테스트].",
            "make.",  # Reload
            "테스트_사실(_Y).",  # Should get modified
        ]

        stdout2, stderr2, returncode2 = self.run_prolog_commands(commands2)

        self.assertIn("원본", stdout1)
        self.assertIn("새로운", stdout2)

    def test_multiple_solutions(self):
        content = """좋아함(mary, pizza).
                    좋아함(mary, pasta).
                    좋아함(john, pasta).
                    좋아함(john, salad)."""

        self.create_test_file("다중해.pl", content)

        commands = [
            "[다중해].",
            "좋아함(mary, _X).",
            ";",
            ";",  # Should give multiple solutions, X = pizza, pasta
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("다중해.pl에서 적재했습니다", stdout)
        self.assertIn("_X = pizza", stdout)
        self.assertIn("_X = pasta", stdout)

    def test_read_write(self):
        content = """안녕 :- read(_X), 쓰기(_X)."""
        self.create_test_file("내용.pl", content)

        commands = [
            "[내용].",
            "read(_X).",
            "안녕.",
            "read(x).",
            "쓰기(+(2, 3)).",
            "안녕.",
            "무엇이든.",
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("내용.pl에서 적재했습니다", stdout)
        self.assertIn("안녕", stdout)
        self.assertIn("거짓", stdout)
        self.assertIn("2 + 3", stdout)
        self.assertIn("무엇이든", stdout)

    def test_atomic(self):
        commands = [
            "단순(random).",
            "단순(_X).",
            "단순(3).",
            "단순(흥미로운(prolog)).",
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("참", stdout)
        self.assertIn("거짓", stdout)
        self.assertIn("참", stdout)
        self.assertIn("거짓", stdout)

    def test_integer(self):
        commands = [
            "정수(3).",
            "정수(random).",
            "정수(4.5).",
            "정수(3.0).",
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("참", stdout)
        self.assertIn("거짓", stdout)
        self.assertIn("거짓", stdout)
        self.assertIn("거짓", stdout)

    def test_errsyntax(self):
        content = """출력 :- 쓰기(안녕)"""
        self.create_test_file("오류.pl", content)

        commands = [
            "[오류].",
            "_X := (2+(3*4).",
            "정수(4.5)정수(3.0).",
            "언어(_X) :- 흥미로운(_X) :- 강의(_X).",
            "언어(_X) :- 흥미로운(_X) 강의(_X).",
            '쓰기("안녕).',
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertRaises(ErrPeriod)
        self.assertRaises(ErrParenthesis)
        self.assertRaises(ErrOperator)
        self.assertRaises(ErrParsing)

    def test_errprolog(self):
        commands = [
            "접합(_Y, _X, _L).",
            "_X := _Y / 2.",
            "_X := 3 + 4 * ().",
            "_X := 3 / 0.",
            "_X := 3 + a.",
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertRaises(ErrUninstantiated)
        self.assertRaises(ErrUnexpected)
        self.assertRaises(ErrDivisionByZero)
        self.assertRaises(ErrNotNumber)

    def test_errrepl(self):
        commands = ["목록(자식.pl.", "[무작위].", "쓰기(안녕, 2)."]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertRaises(ErrInvalidCommand)
        self.assertRaises(ErrFileNotFound)
        self.assertRaises(ErrUnknownPredicate)

    def test_findall_basic(self):
        commands = [
            "모두찾기(_X, _X := 5, _L).",  # Single solution
            "모두찾기(_Y, _Y := 2 + 3, _M).",  # Arithmetic expression
            "모두찾기(_A, _A := 10 * 2, _Q).",  # Multiplication
            "모두찾기(_B, length([1,2,3], _B), _R).",  # Using built-in predicate
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("_L = [5]", stdout)
        self.assertIn("_M = [5]", stdout)
        self.assertIn("_Q = [20]", stdout)
        self.assertIn("_R = [3]", stdout)

    def test_findall_multiple(self):
        content = """father(alan, jim).
                     father(alan, carry).
                     father(alan, mary)."""
        self.create_test_file("multiple.pl", content)

        commands = [
            "[multiple].",
            "모두찾기(C, father(alan, C), Children).",  # Single solution
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("multiple.pl에서 적재했습니다", stdout)
        self.assertIn("Children = [jim, carry, mary]", stdout)

    def test_findall_compound_goals(self):
        commands = [
            "모두찾기(_X, (_X := 3, _X > 2), _L).",  # Compound goal with comma
            "모두찾기(_Y, (_Y := 5, _Y =< 10), _M).",  # Multiple conditions
            "모두찾기(_Z, (_Z := 2 * 3, _Z < 10), _N).",  # Arithmetic with comparison
            "모두찾기(_W, (_W := 1 + 1, _W =:= 2), _P).",  # Arithmetic equality
            "모두찾기(_B, (_B := 4, _B 나머지 2 =:= 0), _R).",  # Even number check
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("_L = [3]", stdout)
        self.assertIn("_M = [5]", stdout)
        self.assertIn("_N = [6]", stdout)
        self.assertIn("_P = [2]", stdout)
        self.assertIn("_R = [4]", stdout)

    def test_initialization_directive(self):
        content = """:- 초기화(시스템_시작).
                    시스템_시작 :- 쓰기('시스템이 초기화되었습니다'), nl.
                    메인_목표."""
        self.create_test_file("초기화.pl", content)
        commands = [
            "[초기화].",
            "메인_목표.",  # Some other goal to test normal execution
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("시스템이 초기화되었습니다", stdout)
        self.assertIn("참", stdout)

    def test_initialization_compound_goal(self):
        content = """:- 초기화((쓰기('시작'), nl, 쓰기('끝'), nl))."""  # TODO wont work when wrapped with parens
        self.create_test_file("초기화.pl", content)

        commands = [
            "[초기화].",
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("시작", stdout)
        self.assertIn("끝", stdout)

    def test_initialization_with_arithmetic(self):
        content = """:- 초기화((_X := 2 + 3, 쓰기(_X)))."""
        self.create_test_file("초기화.pl", content)
        commands = [
            "[초기화].",
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("5", stdout)

    def test_setof_basic_functionality(self):
        content = """
        좋아함(mary, pizza).
        좋아함(mary, pasta).
        좋아함(mary, pizza).
        좋아함(john, pizza).
        좋아함(john, salad).
        좋아함(sue, pasta).
        
        숫자(1).
        숫자(3).
        숫자(2).
        숫자(1).
        숫자(3).
        """

        self.create_test_file("집합.pl", content)

        commands = [
            "[집합].",
            # Test duplicate removal and sorting
            "집합(_X, 좋아함(mary, _X), _결과1).",
            # Test with numbers (sorting)
            "집합(_Y, 숫자(_Y), _결과2).",
            # Test failure when no solutions
            "집합(_Z, 좋아함(bob, _Z), _결과3).",
            # Test single result
            "집합(_W, 좋아함(sue, _W), _결과4).",
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("집합.pl에서 적재했습니다", stdout)
        self.assertIn("_결과1 = [pasta, pizza]", stdout)
        self.assertIn("_결과2 = [1, 2, 3]", stdout)
        self.assertIn("거짓", stdout)
        self.assertIn("_결과4 = [pasta]", stdout)

    def test_setof_vs_findall_comparison(self):
        content = """
        색깔(빨강).
        색깔(파랑).
        색깔(빨강).
        색깔(초록).
        색깔(파랑).
        
        동물(개).
        동물(고양이).
        동물(개).
        """

        self.create_test_file("비교.pl", content)

        commands = [
            "[비교].",
            # Compare findall vs setof for same query
            "모두찾기(_색, 색깔(_색), _모든색깔).",
            "집합(_색, 색깔(_색), _집합색깔).",
            # Test with different data
            "모두찾기(_동물, 동물(_동물), _모든동물).",
            "집합(_동물, 동물(_동물), _집합동물).",
            # Test empty case - findall succeeds, setof fails
            "모두찾기(_새, 새(_새), _모든새).",
            "집합(_새, 새(_새), _집합새).",
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("비교.pl에서 적재했습니다", stdout)

        self.assertIn("_모든색깔 = [빨강, 파랑, 빨강, 초록, 파랑]", stdout)

        self.assertIn("_집합색깔 = [", stdout)
        self.assertIn("빨강", stdout)
        self.assertIn("파랑", stdout)
        self.assertIn("초록", stdout)
        self.assertIn("_모든동물 = [개, 고양이, 개]", stdout)
        self.assertIn("_집합동물 = [개, 고양이]", stdout)
        self.assertIn("_모든새 = []", stdout)

    def test_forall_success(self):
        content = """likes(alice, apples).
                    likes(alice, bananas).
                    likes(alice, cherries).
                    fruit(apples).
                    fruit(bananas).
                    fruit(cherries).
                """

        self.create_test_file("forall_success.pl", content)

        commands = ["[forall_success].", "forall(likes(alice, X), fruit(X))."]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("참", stdout)

    def test_forall_failure(self):
        content = """likes(bob, apples).
                    likes(bob, icecream).
                    fruit(apples).
                """

        self.create_test_file("forall_failure.pl", content)

        commands = ["[forall_failure].", "forall(likes(bob, X), fruit(X))."]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("거짓", stdout)

    def test_forall_vacuous(self):
        content = """fruit(apples).
                    fruit(bananas).
                """  # No likes(claire, _) facts

        self.create_test_file("forall_vacuous.pl", content)

        commands = ["[forall_vacuous].", "forall(likes(claire, X), fruit(X))."]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("참", stdout)

    def test_forall_nested_test(self):
        content = """parent(john, mary).
                    parent(john, bob).
                    human(mary).
                    human(bob).
                """

        self.create_test_file("forall_nested.pl", content)

        commands = ["[forall_nested].", "forall(parent(john, X), human(X))."]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("참", stdout)

    def test_maplist_binding(self):
        commands = [
            "maplist(=, [1, 2], [1, 2]).",
            "maplist(=, [1, 2, 3], [A, B, C]).",
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("참", stdout)
        self.assertIn("A = 1", stdout)
        self.assertIn("B = 2", stdout)
        self.assertIn("C = 3", stdout)

    def test_maplist_add_one(self):
        content = """
            add_one(X, Y) :- Y is X + 1.
        """

        self.create_test_file("maplist_add_one.pl", content)

        commands = [
            "[maplist_add_one].",
            "maplist(add_one, [1, 2, 3], [2, 3, 4]).",
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("참", stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
