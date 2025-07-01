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
            "X is 2 + 3.",  # Testing addition, should be 5
            "Y is 10 - 4.",  # Testing subtraction, should be 6
            "Z is 3 * 4.",  # Testing multiplication, should be 12
            "W is 15 / 3.",  # Testing division, should be 5
            "A is 17 // 5.",  # Testing integer division, should be 3
            "B is 17 mod 5.",  # Testing mod, should be 2
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
            "X is 2 + 3 * 4.",  # Testing precedence, should be 14, not 20
            "Y is 8 / 4 / 2.",  # Testing associativity, should be 1 (left associative)
            "Z is (2 + 3) * 4.",  # Testing parantheses, should be 20
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("X = 14", stdout)
        self.assertIn("Y = 1", stdout)
        self.assertIn("Z = 20", stdout)

    def test_comparison_operators(self):
        commands = [
            "5 =:= 2 + 3.",  # Testing =:=, should be True
            "5 =\\= 6.",  # Testing =\\=, should be True
            "3 < 5.",  # Testing <, should be True
            "5 > 3.",  # Testing >, should be True
            "5 >= 5.",  # Testing >=, should be True
            "5 =< 5.",  # Testing =<, should be True
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertNotIn("False", stdout)

    def test_unification_operator(self):
        commands = [
            "X = 5.",  # Testing basic unification
            "Y = hello.",  # Testing basic unification with constant
            "f(A, B) = f(1, 2).",  # Testing unification with predicates
            "a(b, C, d(e, F, g(h, i, J))) = a(B, c, d(E, f, g(H, i, j))).",  # Testing complex unification with nested predicates
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
        self.assertTrue("ERROR" in stderr or "Error" in stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
