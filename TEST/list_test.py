import os
import subprocess
import tempfile
import unittest


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

    def test_list(self):
        content = """sum([], 0).
                     sum([H|T], X) :- sum(T,Y), X is H + Y."""

        self.create_test_file("list.txt", content)

        commands = [
            "[list].",
            "sum([1,2,3,4], X).",  # Testing H|T structure and recursion, should give 10
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("X = 10", stdout)

    def test_list_append(self):
        commands = [
            "append([1,2],[3,4], L).",  # Testing append with two nonempty lists and variable, should work
            "append([], [1,2], X).",  # Testing append with one empty and one nonempty list, should work
            "append([3,4],[], X).",  # Testing append with one nonempty and one empty list, should work
            "append([1,2],[3,4], []).",  # Testing append with two nonempty lists with empty list, should not work
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("L = [1, 2, 3, 4]", stdout)
        self.assertIn("X = [1, 2]", stdout)
        self.assertIn("X = [3, 4]", stdout)
        self.assertIn("False", stdout)

    def test_list_length(self):
        commands = ["length([1,2,3], X).", "length(L, 4)."]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("X = 3", stdout)
        self.assertIn("L = [_, _, _, _]", stdout)

    def test_list_permutation(self):
        commands = [
            "permutation([1,2,3], X).",  # Testing permutation with second parameter being a Variable
            ";",
            ";",
            ";",
            ";",
            ";",
            ";",
            "permutation(L, [6,7]).",  # Testing permutation with first parameter being a Variable
            ";",
            ";",
            "permutation([2,3,4,5], [4,3,5,2]).",  # Testing permutation True/False
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("X = [1, 2, 3]", stdout)
        self.assertIn("X = [1, 3, 2]", stdout)
        self.assertIn("X = [2, 1, 3]", stdout)
        self.assertIn("X = [2, 3, 1]", stdout)
        self.assertIn("X = [3, 1, 2]", stdout)
        self.assertIn("X = [3, 2, 1]", stdout)
        self.assertIn("L = [6, 7]", stdout)
        self.assertIn("L = [7, 6]", stdout)
        self.assertIn("True", stdout)

    # def test_n_queens(self):


if __name__ == "__main__":
    unittest.main(verbosity=2)
