import unittest
import subprocess
import tempfile
import os


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

    def test_basic_arithmetic_operators(self):
        commands = [
            "X is 2 + 3.",
            "Y is 10 - 4.",
            "Z is 3 * 4.",
            "W is 15 / 3.",
            "A is 17 // 5.",
            "B is 17 mod 5.",
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("X = 5", stdout)
        self.assertIn("Y = 6", stdout)
        self.assertIn("Z = 12", stdout)
        self.assertIn("W = 5", stdout)
        self.assertIn("A = 3", stdout)
        self.assertIn("B = 2", stdout)

    def test_arithmetic_precedence(self):
        commands = [
            "X is 2 + 3 * 4.",  # Should be 14, not 20
            "Y is 8 / 4 / 2.",  # Should be 1 (left associative)
            "Z is (2 + 3) * 4.",  # Should be 20
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("X = 14", stdout)
        self.assertIn("Y = 1", stdout)
        self.assertIn("Z = 20", stdout)

    def test_comparison_operators(self):
        commands = [
            "5 =:= 2 + 3.",  # all should succeed
            "5 =\\= 6.",
            "3 < 5.",
            "5 > 3.",
            "5 >= 5.",
            "5 =< 5.",
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertNotIn("False", stdout)

    def test_unification_operator(self):
        commands = [
            "X = 5.",
            "Y = hello.",
            "f(A, B) = f(1, 2).",
            "a(b, C, d(e, F, g(h, i, J))) = a(B, c, d(E, f, g(H, i, j)))."
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("X = 5", stdout)
        self.assertIn("Y = hello", stdout)
        self.assertIn("A = 1", stdout)
        self.assertIn("B = 2", stdout)
        self.assertIn("C = c", stdout)
        self.assertIn("F = f", stdout)
        self.assertIn("J = j", stdout)
        self.assertIn("B = b", stdout)
        self.assertIn("E = e", stdout)
        self.assertIn("H = h", stdout)



    def test_file_loading_and_facts(self):
        content = """parent(john, mary).
                    parent(john, tom).
                    parent(sue, mary).
                    parent(sue, tom).
                    likes(mary, pizza).
                    likes(john, pasta)."""

        self.create_test_file("facts.txt", content)

        commands = [
            "[facts].",  # Load the file
            "parent(john, mary).",  # Should succeed
            "parent(mary, john).",  # Should fail
            "parent(john, X).",  # Should give multiple solutions
            "likes(mary, pizza).",  # Should succeed
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("loaded from facts.txt", stdout)
        self.assertIn("True", stdout)
        self.assertIn("False", stdout)

    def test_simple_rules(self):
        content = """parent(john, mary).
                    parent(mary, sue).
                    grandparent(X, Z) :- parent(X, Y), parent(Y, Z)."""

        self.create_test_file("rules.txt", content)

        commands = [
            "[rules].",
            "grandparent(john, sue).",  # Should succeed
            "grandparent(john, X).",  # Should bind X to sue
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("loaded from rules.txt", stdout)

    def test_recursive_factorial(self):
        content = """factorial(0, 1).
                    factorial(N, Result) :- N > 0, N1 is N - 1, factorial(N1, SubResult), Result is N * SubResult."""

        self.create_test_file("factorial.txt", content)

        commands = [
            "[factorial].",
            "factorial(5, X).",  # Should give X = 120
            "factorial(0, Y).",  # Should give Y = 1
            "factorial(3, Z).",  # Should give Z = 6
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("loaded from factorial.txt", stdout)
        self.assertIn("X = 120", stdout)
        self.assertIn("Y = 1", stdout)
        self.assertIn("Z = 6", stdout)

    def test_recursive_sum(self):
        content = """sum_to(0, 0).
                    sum_to(N, Result) :- N > 0, N1 is N - 1, sum_to(N1, SubResult), Result is N + SubResult."""

        self.create_test_file("sum.txt", content)

        commands = [
            "[sum].",
            "sum_to(5, X).",  # Should give X = 15 (0+1+2+3+4+5)
            "sum_to(3, Y).",  # Should give Y = 6 (0+1+2+3)
            "sum_to(0, Z).",  # Should give Z = 0
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("loaded from sum.txt", stdout)
        self.assertIn("X = 15", stdout)
        self.assertIn("Y = 6", stdout)
        self.assertIn("Z = 0", stdout)

    def test_conjunction_comma(self):
        content = """parent(john, mary).
                    parent(mary, sue).
                    male(john).
                    female(mary).
                    female(sue)."""

        self.create_test_file("conjunction.txt", content)

        commands = [
            "[conjunction].",
            "parent(john, mary), female(mary).",  # Both should be true
            "parent(john, mary), male(mary).",  # Should fail
            "parent(X, Y), female(Y).",  # Should find solutions
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("loaded from conjunction.txt", stdout)
        # First query should succeed, second should fail

    def test_disjunction_semicolon(self):
        content = """likes(mary, pizza).
                    likes(john, pasta).
                    likes(sue, salad)."""

        self.create_test_file("disjunction.txt", content)

        commands = [
            "[disjunction].",
            "likes(mary, pizza); likes(mary, pasta).",  # First part true
            "likes(mary, soup); likes(mary, pizza).",  # Second part true
            "likes(mary, soup); likes(mary, bread).",  # Both false
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("loaded from disjunction.txt", stdout)
        # First two should succeed, third should fail

    def test_nested_expressions(self):
        commands = [
            "X is (2 + 3) * (4 - 1).",  # Should be 15
            "Y is 2 + (3 * (4 + 1)).",  # Should be 17
            "Z is ((8 / 4) + 1) * 3.",  # Should be 9
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("X = 15", stdout)
        self.assertIn("Y = 17", stdout)
        self.assertIn("Z = 9", stdout)

    def test_error_cases(self):
        commands = [
            "X is Y + 3.",  # Y uninstantiated - should error
            "X is 5 / 0.",  # Division by zero - should error
            "atom =:= 5.",  # Type error - should error
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        # Should contain error messages
        self.assertTrue(
            "ERROR" in stdout
            or "Error" in stdout
            or "error" in stdout
            or "ERROR" in stderr
            or "Error" in stderr
            or "error" in stderr
        )

    def test_make_reload(self):
        # Create initial file
        content1 = "test_fact(original)."
        filepath = self.create_test_file("reload_test.txt", content1)

        commands = [
            "[reload_test].",
            "test_fact(X).",  # Should get original
        ]

        stdout1, stderr1, returncode1 = self.run_prolog_commands(commands)

        # Modify the file
        content2 = "test_fact(modified)."
        with open(filepath, "w") as f:
            f.write(content2)

        commands2 = [
            "[reload_test].",
            "make.",  # Reload
            "test_fact(Y).",  # Should get modified
        ]

        stdout2, stderr2, returncode2 = self.run_prolog_commands(commands2)

        self.assertIn("original", stdout1)
        self.assertIn("modified", stdout2)

    def test_multiple_solutions(self):
        content = """likes(mary, pizza).
                    likes(mary, pasta).
                    likes(john, pasta).
                    likes(john, salad)."""

        self.create_test_file("multiple.txt", content)

        commands = [
            "[multiple].",
            "likes(mary, X).",  # should give X = pizza; X = pasta
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("loaded from multiple.txt", stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
