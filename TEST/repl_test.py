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

    def test_file_loading_and_facts(self):
        content = """parent(john, mary).
                    parent(john, tom).
                    parent(sue, mary).
                    parent(sue, tom).
                    likes(mary, pizza).
                    likes(john, pasta)."""

        self.create_test_file("facts.txt", content)

        commands = [
            "[facts].",
            "parent(john, mary).",  # Should succeed
            "parent(mary, john).",  # Should fail
            "parent(john, X).",
            ";",";",  # Should give multiple solutions (mary, tom)
            "likes(mary, pizza).",  # Should succeed
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("loaded from facts.txt", stdout)
        self.assertIn("True", stdout)
        self.assertIn("False", stdout)
        self.assertIn("X = mary", stdout)
        self.assertIn("X = tom", stdout)
        self.assertIn("True", stdout)

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
                     female(mary).
                     female(sue).
                     mother(X) :- parent(Y, X), female(X).
                     """

        self.create_test_file("conjunction.txt", content)

        commands = [
            "[conjunction].",
            "mother(X).",
            ";", ";"  # Should give multiple solutions, X = mary, sue
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("loaded from conjunction.txt", stdout)
        self.assertIn("X = mary", stdout)
        self.assertIn("X = sue", stdout)

    def test_disjunction_semicolon(self):
        content = """language(prolog).
                     language(c).
                     lecture(prolog).
                     lecture(python).
                     interesting(X) :- language(X); lecture(X)."""

        self.create_test_file("disjunction.txt", content)

        commands = [
            "[disjunction].",
            "interesting(X).",
            ";", ";", ";"
        ]  # Should give multiple solutions, X = prolog, c, python

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("loaded from disjunction.txt", stdout)
        self.assertIn("X = prolog", stdout)
        self.assertIn("X = c", stdout)
        self.assertIn("X = python", stdout)

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
            "likes(mary, X).",
            ";", ";"  # Should give multiple solutions, X = pizza, pasta
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("loaded from multiple.txt", stdout)
        self.assertIn("X = pizza", stdout)
        self.assertIn("X = pasta", stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
