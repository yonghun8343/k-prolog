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
        with open(filepath, "w", encoding="utf-8") as f:
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

        self.create_test_file("리스트.kpl", content)

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
            "순열(_리스트, [6,7]).",  # Testing permutation with first parameter being a Variable
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

    def test_member(self):
        commands = [
            "원소(1, [1,2,3]).",  # Testing member with first element
            "원소(3, [1,2,3]).",  # Testing member with last element
            "원소(2, [1,2,3]).",  # Testing member with middle element
            "원소(4, [1,2,3]).",  # Testing member with non-existent element, should fail
            "원소(_엑스, [1,2,3]).",  # Testing member with variable, should give first solution
            ";",  # Get next solution
            ";",  # Get next solution
            "원소(a, [a|b]).",
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn(
            "참", stdout
        )  # Should have multiple 참 for successful matches
        self.assertIn(
            "거짓", stdout
        )  # Should have 거짓 for non-existent element
        self.assertIn("_엑스 = 1", stdout)  # First solution
        self.assertIn("_엑스 = 2", stdout)  # Second solution
        self.assertIn("_엑스 = 3", stdout)  # Third solution
        self.assertIn("참", stdout)

    def test_sort(self):
        commands = [
            "정렬([3,1,4,1,5], _결과).",  # Testing sort with duplicates
            "정렬([1,2,3], _결과2).",  # Testing sort with already sorted list
            "정렬([3,2,1], _결과3).",  # Testing sort with reverse order
            "정렬([], _결과4).",  # Testing sort with empty list
            "정렬([1], _결과5).",  # Testing sort with single element
            "정렬([a,c,b,a], _결과6).",  # Testing sort with atoms and duplicates
            "정렬([3,1,4,1,5], [1,3,4,5]).",  # Testing sort with expected result (should succeed)
            "정렬([3,1,4,1,5], [1,1,3,4,5]).",  # Testing sort with wrong expected result (should fail)
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn(
            "참", stdout
        )  # Should have multiple 참 for successful sorts
        self.assertIn(
            "거짓", stdout
        )  # Should have 거짓 for wrong expected result
        self.assertIn(
            "_결과 = [1, 3, 4, 5]", stdout
        )  # Sorted with duplicates removed
        self.assertIn("_결과2 = [1, 2, 3]", stdout)  # Already sorted list
        self.assertIn("_결과3 = [1, 2, 3]", stdout)  # Reverse order sorted
        self.assertIn("_결과4 = []", stdout)  # Empty list result
        self.assertIn("_결과5 = [1]", stdout)  # Single element result
        self.assertIn(
            "_결과6 = [a, b, c]", stdout
        )  # Atoms sorted with duplicates removed

    def test_keysort(self):
        commands = [
            "키정렬([3-a, 1-b, 2-c], _결과).",  # Testing keysort with key-value pairs
            "키정렬([1-x, 1-y, 2-z], _결과2).",  # Testing keysort with duplicate keys
            "키정렬([c-3, a-1, b-2], _결과3).",  # Testing keysort with atom keys
            "키정렬([], _결과4).",  # Testing keysort with empty list
            "키정렬([1-only], _결과5).",  # Testing keysort with single pair
            "키정렬([2-b, 1-a, 3-c], [1-a, 2-b, 3-c]).",  # Testing keysort with expected result (should succeed)
            "키정렬([2-b, 1-a, 3-c], [1-a, 3-c, 2-b]).",  # Testing keysort with wrong order (should fail)
            "키정렬([3-x, 1-y, 1-z, 2-w], _결과6).",  # Testing keysort preserving duplicate keys
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn(
            "참", stdout
        )  # Should have multiple 참 for successful keysorting
        self.assertIn(
            "거짓", stdout
        )  # Should have 거짓 for wrong expected order
        self.assertIn("_결과 = [1-b, 2-c, 3-a]", stdout)  # Sorted by keys
        self.assertIn(
            "_결과2 = [1-x, 1-y, 2-z]", stdout
        )  # Duplicate keys preserved in order
        self.assertIn("_결과3 = [a-1, b-2, c-3]", stdout)  # Atom keys sorted
        self.assertIn("_결과4 = []", stdout)  # Empty list result
        self.assertIn("_결과5 = [1-only]", stdout)  # Single pair result
        self.assertIn(
            "_결과6 = [1-y, 1-z, 2-w, 3-x]", stdout
        )  # Duplicate keys in stable order

    def test_flatten(self):
        commands = [
            "평평히([1,2,[3],[4,[5]]], _결과).",  # Testing flatten with nested lists
            "평평히([1,[2,3],[[4]]], _결과2).",  # Testing flatten with more complex nesting
            "평평히([a,[b,[c,d]],e], _결과3).",  # Testing flatten with atoms
            "평평히([], _결과4).",  # Testing flatten with empty list
            "평평히([1,2,3], _결과5).",  # Testing flatten with already flat list
            "평평히([[],[1],[],[2,3],[]], _결과6).",  # Testing flatten with empty sublists
            "평평히([1,2,[3]], [1,2,3]).",  # Testing flatten verification (should succeed)
            "평평히([1,[2,3]], [1,2,4]).",  # Testing flatten wrong verification (should fail)
            "평평히(_엑스, [1,2,3]).",  # Testing flatten with variable first param (should fail)
            "평평히(_엑스, _와이).",  # Testing flatten with both variables (special case)
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn(
            "참", stdout
        )  # Should have multiple 참 for successful flattening
        self.assertIn(
            "거짓", stdout
        )  # Should have 거짓 for wrong verification and variable first param
        self.assertIn(
            "_결과 = [1, 2, 3, 4, 5]", stdout
        )  # Nested lists flattened
        self.assertIn(
            "_결과2 = [1, 2, 3, 4]", stdout
        )  # Complex nesting flattened
        self.assertIn("_결과3 = [a, b, c, d, e]", stdout)  # Atoms flattened
        self.assertIn("_결과4 = []", stdout)  # Empty list remains empty
        self.assertIn(
            "_결과5 = [1, 2, 3]", stdout
        )  # Already flat list unchanged
        self.assertIn("_결과6 = [1, 2, 3]", stdout)  # Empty sublists removed
        self.assertIn("_와이 = [_엑스]", stdout)  # Special case: both variables

    def test_between(self):
        commands = [
            "이내(1, 3, _엑스).",  # Testing between with variable - should generate 1, 2, 3
            ";",
            ";",
            "이내(5, 8, _와이).",  # Testing between with different range
            ";",
            ";",
            ";",
            "이내(1, 5, 3).",  # Testing between verification (should succeed)
            "이내(1, 5, 7).",  # Testing between verification (should fail - out of range)
            "이내(2, 2, 2).",  # Testing between with same low and high (should succeed)
            "이내(3, 1, 2).",  # Testing between with high < low (should fail)
            "이내(0, 0, 0).",  # Testing between with zero values (should succeed)
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn(
            "참", stdout
        )  # Should have multiple 참 for successful between checks
        self.assertIn(
            "거짓", stdout
        )  # Should have 거짓 for out of range and invalid range
        self.assertIn(
            "_엑스 = 1", stdout
        )  # First solution for between(1, 3, X)
        self.assertIn(
            "_엑스 = 2", stdout
        )  # Second solution for between(1, 3, X)
        self.assertIn(
            "_엑스 = 3", stdout
        )  # Third solution for between(1, 3, X)
        self.assertIn(
            "_와이 = 5", stdout
        )  # First solution for between(5, 8, Y)
        self.assertIn(
            "_와이 = 6", stdout
        )  # Second solution for between(5, 8, Y)
        self.assertIn(
            "_와이 = 7", stdout
        )  # Third solution for between(5, 8, Y)
        self.assertIn(
            "_와이 = 8", stdout
        )  # Fourth solution for between(5, 8, Y)

    def test_ord_subset(self):
        commands = [
            "서열부분집합([1, 3], [1, 2, 3, 4]).",  # Testing valid ordered subsequence (should succeed)
            "서열부분집합([3, 1], [1, 2, 3, 4]).",  # Testing invalid subsequence - wrong order (should fail)
            "서열부분집합([1, 2, 4], [1, 2, 3, 4]).",  # Testing valid ordered subsequence (should succeed)
            "서열부분집합([2, 3, 5], [1, 2, 3, 4]).",  # Testing invalid subsequence - element not in set (should fail)
            "서열부분집합([], [1, 2, 3]).",  # Testing empty subset (should succeed)
            "서열부분집합([1, 2, 3], []).",  # Testing non-empty subset of empty set (should fail)
            "서열부분집합([], []).",  # Testing empty subset of empty set (should succeed)
            "서열부분집합([a, c], [a, b, c, d]).",  # Testing with atoms (should succeed)
            "서열부분집합([c, a], [a, b, c, d]).",  # Testing with atoms - wrong order (should fail)
            "서열부분집합([1, 2, 3], [1, 2, 3]).",  # Testing identical lists (should succeed)
            "서열부분집합(_부분집합, [1, 2, 3]).",  # Testing with variable subset (generates empty list)
            "서열부분집합([1, 2], _집합).",  # Testing with variable set (unifies set with subset)
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn(
            "참", stdout
        )  # Should have multiple 참 for successful checks
        self.assertIn("거짓", stdout)  # Should have 거짓 for failed checks
        self.assertIn(
            "_부분집합 = []", stdout
        )  # Variable subset generates empty list
        self.assertIn(
            "_집합 = [1, 2|", stdout
        )  # Variable set unifies with subset with tail

    def test_select(self):
        commands = [
            "선택(10, [1, 2, 3], _나머지).",  # Testing element not in list (should fail)
            "선택(2, [1, 2, 3], _나머지1).",  # Testing element in list - single occurrence
            "선택(2, [1, 2, 3, 2, 4], _나머지2).",  # Testing element with multiple occurrences - first solution
            ";",  # Get second solution for multiple occurrences
            "선택(2, [1, 2, 3, 2, 4, 2], _나머지3).",  # Testing element with three occurrences - first solution
            ";",
            ";",
            "선택(a, [a], _나머지4).",  # Testing single element list
            "선택(b, [a], _나머지5).",  # Testing element not in single element list (should fail)
            "선택(1, [1, 1, 1], _나머지6).",  # Testing all same elements - first solution
            ";",
            ";",
            "선택(x, [x, y, z], [y, z]).",  # Testing verification mode (should succeed)
            "선택(x, [x, y, z], [x, y]).",  # Testing verification mode - wrong result (should fail)
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn(
            "참", stdout
        )  # Should have multiple 참 for successful selections
        self.assertIn("거짓", stdout)  # Should have 거짓 for failed selections
        self.assertIn("_나머지1 = [1, 3]", stdout)  # Single occurrence removal
        self.assertIn(
            "_나머지2 = [1, 3, 2, 4]", stdout
        )  # First occurrence removal
        self.assertIn(
            "_나머지2 = [1, 2, 3, 4]", stdout
        )  # Second occurrence removal
        self.assertIn(
            "_나머지3 = [1, 3, 2, 4, 2]", stdout
        )  # First of three occurrences
        self.assertIn(
            "_나머지3 = [1, 2, 3, 4, 2]", stdout
        )  # Second of three occurrences
        self.assertIn(
            "_나머지3 = [1, 2, 3, 2, 4]", stdout
        )  # Third of three occurrences
        self.assertIn(
            "_나머지4 = []", stdout
        )  # Single element removal leaves empty list
        self.assertIn(
            "_나머지6 = [1, 1]", stdout
        )  # Remove first of three identical elements


if __name__ == "__main__":
    unittest.main(verbosity=2)
