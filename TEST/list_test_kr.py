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

    def test_list(self):
        content = """합집([], 0).
                     합집([_머리|_꼬리], _엑스) :- 합집(_꼬리,_와이), _엑스 := _머리 + _와이."""

        self.create_test_file("리스트.pl", content)

        commands = [
            "[리스트].",
            "합집([1,2,3,4], _엑스).",  # Testing H|T structure and recursion, should give 10
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("_엑스 = 10", stdout)

    def test_list_append(self):
        commands = [
            "접합([1,2],[3,4], _리스트).",  # Testing append with two nonempty lists and variable, should work
            "접합([], [1,2], _엑스).",  # Testing append with one empty and one nonempty list, should work
            "접합([3,4],[], _엑스).",  # Testing append with one nonempty and one empty list, should work
            "접합([1,2],[3,4], []).",  # Testing append with two nonempty lists with empty list, should not work
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("_리스트 = [1, 2, 3, 4]", stdout)
        self.assertIn("_엑스 = [1, 2]", stdout)
        self.assertIn("_엑스 = [3, 4]", stdout)
        self.assertIn("거짓", stdout)

    def test_list_length(self):
        commands = ["길이([1,2,3], _엑스).", "길이(_리스트, 4)."]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("_엑스 = 3", stdout)
        self.assertIn("_리스트 = [_, _, _, _]", stdout)

    def test_list_permutation(self):
        commands = [
            "순열([1,2,3], _엑스).",  # Testing permutation with second parameter being a Variable
            ";",
            ";",
            ";",
            ";",
            ";",
            ";",
            "순열(_리스트, [6,7]).",  # Testing permutation with first parameter being a Variable
            ";",
            ";",
            "순열([2,3,4,5], [4,3,5,2]).",  # Testing permutation True/False
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("_엑스 = [1, 2, 3]", stdout)
        self.assertIn("_엑스 = [1, 3, 2]", stdout)
        self.assertIn("_엑스 = [2, 1, 3]", stdout)
        self.assertIn("_엑스 = [2, 3, 1]", stdout)
        self.assertIn("_엑스 = [3, 1, 2]", stdout)
        self.assertIn("_엑스 = [3, 2, 1]", stdout)
        self.assertIn("_리스트 = [6, 7]", stdout)
        self.assertIn("_리스트 = [7, 6]", stdout)
        self.assertIn("참", stdout)

    # def test_n_queens(self):


if __name__ == "__main__":
    unittest.main(verbosity=2)
