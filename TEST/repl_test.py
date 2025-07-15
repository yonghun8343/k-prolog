import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import subprocess
import tempfile
import unittest

from err import *


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
        input_text = "\n".join(commands) + "\nhalt.\n"
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
        content = """parent(john, mary).
                    parent(john, tom).
                    parent(sue, mary).
                    parent(sue, tom).
                    likes(mary, pizza).
                    likes(john, pasta)."""

        self.create_test_file("facts.pl", content)

        commands = [
            "[facts].",
            "parent(john, mary).",  # Should succeed
            "parent(mary, john).",  # Should fail
            "parent(john, X).",
            ";",
            ";",  # Should give multiple solutions (mary, tom)
            "likes(mary, pizza).",  # Should succeed
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("loaded from facts.pl", stdout)
        self.assertIn("True", stdout)
        self.assertIn("False", stdout)
        self.assertIn("X = mary", stdout)
        self.assertIn("X = tom", stdout)
        self.assertIn("True", stdout)

    def test_recursive_factorial(self):
        content = """factorial(0, 1).
                    factorial(N, Result) :- N > 0, N1 is N - 1, factorial(N1, SubResult), Result is N * SubResult."""

        self.create_test_file("factorial.pl", content)

        commands = [
            "[factorial].",
            "factorial(5, X).",  # Should give X = 120
            "factorial(0, Y).",  # Should give Y = 1
            "factorial(3, Z).",  # Should give Z = 6
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("loaded from factorial.pl", stdout)
        self.assertIn("X = 120", stdout)
        self.assertIn("Y = 1", stdout)
        self.assertIn("Z = 6", stdout)

    def test_recursive_sum(self):
        content = """sum_to(0, 0).
                    sum_to(N, Result) :- N > 0, N1 is N - 1, sum_to(N1, SubResult), Result is N + SubResult."""

        self.create_test_file("sum.pl", content)

        commands = [
            "[sum].",
            "sum_to(5, X).",  # Should give X = 15 (0+1+2+3+4+5)
            "sum_to(3, Y).",  # Should give Y = 6 (0+1+2+3)
            "sum_to(0, Z).",  # Should give Z = 0
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("loaded from sum.pl", stdout)
        self.assertIn("X = 15", stdout)
        self.assertIn("Y = 6", stdout)
        self.assertIn("Z = 0", stdout)

    def test_conjunction_comma(self):
        content = """parent(john, mary).
                     parent(mary, sue).
                     female(mary).
                     female(sue).
                     mother(X) :- parent(Y, X), female(X).
                     """

        self.create_test_file("conjunction.pl", content)

        commands = [
            "[conjunction].",
            "mother(X).",
            ";",
            ";",  # Should give multiple solutions, X = mary, sue
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("loaded from conjunction.pl", stdout)
        self.assertIn("X = mary", stdout)
        self.assertIn("X = sue", stdout)

    def test_disjunction_semicolon(self):
        content = """language(prolog).
                     language(c).
                     lecture(prolog).
                     lecture(python).
                     interesting(X) :- language(X); lecture(X)."""

        self.create_test_file("disjunction.pl", content)

        commands = [
            "[disjunction].",
            "interesting(X).",
            ";",
            ";",
            ";",
        ]  # Should give multiple solutions, X = prolog, c, python

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("loaded from disjunction.pl", stdout)
        self.assertIn("X = prolog", stdout)
        self.assertIn("X = c", stdout)
        self.assertIn("X = python", stdout)

    def test_make_reload(self):
        # Create initial file
        content1 = "test_fact(original)."
        filepath = self.create_test_file("reload_test.pl", content1)

        commands = [
            "[reload_test].",
            "test_fact(X).",  # Should get original
        ]

        stdout1, stderr1, returncode1 = self.run_prolog_commands(commands)

        # Modify the file
        content2 = "test_fact(new)."
        with open(filepath, "w") as f:
            f.write(content2)

        commands2 = [
            "[reload_test].",
            "make.",  # Reload
            "test_fact(Y).",  # Should get modified
        ]

        stdout2, stderr2, returncode2 = self.run_prolog_commands(commands2)

        self.assertIn("original", stdout1)
        self.assertIn("new", stdout2)

    def test_multiple_solutions(self):
        content = """likes(mary, pizza).
                    likes(mary, pasta).
                    likes(john, pasta).
                    likes(john, salad)."""

        self.create_test_file("multiple.pl", content)

        commands = [
            "[multiple].",
            "likes(mary, X).",
            ";",
            ";",  # Should give multiple solutions, X = pizza, pasta
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("loaded from multiple.pl", stdout)
        self.assertIn("X = pizza", stdout)
        self.assertIn("X = pasta", stdout)

    def test_read_write(self):
        content = """hello :- read(X), write(X)."""
        self.create_test_file("content.pl", content)

        commands = [
            "[content].",
            "read(X).",
            "hello.",
            "read(x).",
            "write(+(2, 3)).",
            "hello.",
            "whatever.",
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("loaded from content.pl", stdout)
        self.assertIn("hello", stdout)
        self.assertIn("False", stdout)
        self.assertIn("2 + 3", stdout)
        self.assertIn("whatever", stdout)

    def test_atomic(self):
        commands = [
            "atomic(random).",
            "atomic(X).",
            "atomic(3)",
            "atomic(interesting(prolog)).",
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("True", stdout)
        self.assertIn("False", stdout)
        self.assertIn("True", stdout)
        self.assertIn("False", stdout)

    def test_integer(self):
        commands = [
            "integer(3).",
            "integer(random).",
            "integer(4.5)integer(3.0).",
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("True", stdout)
        self.assertIn("False", stdout)
        self.assertIn("False", stdout)
        self.assertIn("False", stdout)

    def test_errsyntax(self):
        content = """print :- write(hello)"""
        self.create_test_file("faulty.pl", content)

        commands = [
            "[faulty].",
            "X is (2+(3*4).",
            "integer(4.5)integer(3.0).",
            "language(X) :- interesting(X) :- lecture(X).",
            "language(X) :- interesting(X) lecture(X).",
            'write("hello).',
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertRaises(ErrPeriod)
        self.assertRaises(ErrParenthesis)
        self.assertRaises(ErrOperator)
        self.assertRaises(ErrParsing)

    def test_errprolog(self):
        commands = [
            "append(Y, X, L).",
            "X is Y / 2.",
            "X is 3 + 4 * ().",
            "X is 3 / 0.",
            "X is 3 + a.",
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertRaises(ErrUninstantiated)
        self.assertRaises(ErrUnexpected)
        self.assertRaises(ErrDivisionByZero)
        self.assertRaises(ErrNotNumber)

    def test_errrepl(self):
        commands = ["listing(child.pl.", "[random].", "write(hello, 2)."]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertRaises(ErrInvalidCommand)
        self.assertRaises(ErrFileNotFound)
        self.assertRaises(ErrUnknownPredicate)

    def test_findall_basic(self):
        commands = [
            "findall(X, X is 5, L).",  # Single solution
            "findall(Y, Y is 2 + 3, M).",  # Arithmetic expression
            "findall(A, A is 10 * 2, Q).",  # Multiplication
            "findall(B, length([1,2,3], B), R).",  # Using built-in predicate
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("L = [5]", stdout)
        self.assertIn("M = [5]", stdout)
        self.assertIn("Q = [20]", stdout)
        self.assertIn("R = [3]", stdout)

    def test_findall_compound_goals(self):
        commands = [
            "findall(X, (X is 3, X > 2), L).",  # Compound goal with comma
            "findall(Y, (Y is 5, Y =< 10), M).",  # Multiple conditions
            "findall(Z, (Z is 2 * 3, Z < 10), N).",  # Arithmetic with comparison
            "findall(W, (W is 1 + 1, W =:= 2), P).",  # Arithmetic equality
            "findall(B, (B is 4, B mod 2 =:= 0), R).",  # Even number check
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("L = [3]", stdout)
        self.assertIn("M = [5]", stdout)
        self.assertIn("N = [6]", stdout)
        self.assertIn("P = [2]", stdout)
        self.assertIn("R = [4]", stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
