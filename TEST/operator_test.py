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

    def test_anonymous_variables(self):
        content = """
        test_anon(X, _) :- X is 3.
        test_anon2(_, Y) :- Y = 4.
        test_match(_, _).
        """

        self.create_test_file("anon.txt", content)
        commands = [
        "[anon].",
        "test_anon(L, 5).",     
        "test_anon(A, B).",
        "test_anon2(3, 4).",
        "test_anon2(4, 5).",
        "test_match(foo, bar).",        
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("loaded from anon.txt", stdout)

        self.assertIn("L = 3", stdout)
        self.assertIn("A = 3", stdout)
        self.assertIn("True", stdout)
        self.assertIn("False", stdout)
        self.assertIn("True", stdout)
    
    def test_not(self):
        content = """
        red(apple).
        blue(X) :- not(red(X)).
        """

        self.create_test_file("not.txt", content)

        commands = [
            "[not].",
            "blue(apple).",
            "not(15 is (2 + 3) * (4 - 1)).", 
            "not(3 is 1 + 3).",
            "not(X is 4).",
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("loaded from not.txt", stdout)
        self.assertIn("False", stdout)
        self.assertIn("False", stdout)
        self.assertIn("True", stdout)
        self.assertIn("False", stdout)
    
    def test_n_queens(self):
        content = """
        queens(N,Qs) :- range(1,N,Ns), permutation(Ns,Qs), safe(Qs).

        safe([]).
        safe([Q|Qs]) :- safe(Qs), not(attack(Q,Qs)).

        attack(X,Xs) :- attack(X,1,Xs).
        attack(X,N,[Y|_]) :- X is Y+N; X is Y-N.
        attack(X,N,[_|Ys]) :- N1 is N+1, attack(X,N1,Ys).

        range(N,N,[N]).
        range(M,N,[M|Ns]) :- M < N, M1 is M+1, range(M1,N,Ns).
        """

        self.create_test_file("nqueens.txt", content)

        commands = [
            "[nqueens].",
            "queens(4, Qs).",
            ";", ";", 
            # "queens(6, Qs).",  # takes too long
            # ";", ";", ";", ";"
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("loaded from nqueens.txt", stdout)
        self.assertIn("Qs = [2, 4, 1, 3]", stdout)
        self.assertIn("Qs = [3, 1, 4, 2]", stdout)
        # self.assertIn("Qs = [2, 4, 6, 1, 3, 5]", stdout)
        # self.assertIn("Qs = [3, 6, 2, 5, 1, 4]", stdout)
        # self.assertIn("Qs = [4, 1, 5, 2, 6, 3]", stdout)
        # self.assertIn("Qs = [5, 3, 1, 6, 4, 2]", stdout)

    def test_operator_orders(self):
        commands = [
            "X is +(2,3).",
            "Y is +(*(2, 3), 4 + 1).",
            "Z is /(+(6, 4), mod(7, 3)).", 
            "A is +(+(1, 2), *(/(8, 4), 3)).",
            "B is *(+(2, 3), (4 + mod(10, 3))).",
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("X = 5", stdout)
        self.assertIn("Y = 11", stdout)
        self.assertIn("Z = 10", stdout)
        self.assertIn("A = 9", stdout)
        self.assertIn("B = 25", stdout)
    
    def test_cut_operator(self):
        content = """max(X, Y, X) :- X >= Y, !.
                max(X, Y, Y).

                first([H|_], H) :- !.
                first([_|T], X) :- first(T, X).

                choice(a) :- !.
                choice(b).
                choice(c).

                test_cut(1) :- !, fail.
                test_cut(2).

                member_cut(X, [X|_]) :- !.
                member_cut(X, [_|T]) :- member_cut(X, T)."""
        
        self.create_test_file("cut_test.txt", content)
        
        # Should only give one answer
        commands1 = [
            "[cut_test].",
            "max(5, 3, Z).", ";" # Should succeed with Z = 5, no backtracking
        ]
        stdout1, stderr1, returncode1 = self.run_prolog_commands(commands1)
        self.assertIn("Z = 5", stdout1)

        # Should not show multiple solutions due to cut
        commands2 = [
            "[cut_test].", 
            "max(2, 7, Z)."
        ]
        stdout2, stderr2, returncode2 = self.run_prolog_commands(commands2)
        self.assertIn("Z = 7", stdout2)
        

        commands3 = [
            "[cut_test].",
            "choice(X).", ";", ";", ";"  # Should only give X = a due to cut
        ]
        stdout3, stderr3, returncode3 = self.run_prolog_commands(commands3)
        self.assertIn("X = a", stdout3)
        self.assertNotIn("X = b", stdout3)  # Cut should prevent this
        self.assertNotIn("X = c", stdout3)  # Cut should prevent this

    def test_cut_with_backtracking(self):
        content = """p(X) :- q(X), !, r(X).
                    p(X) :- s(X).

                    q(1).
                    q(2).
                    r(1).
                    s(3)."""
        
        self.create_test_file("backtrack_test.txt", content)
        
        commands = [
            "[backtrack_test].",
            "p(1).",  # Should succeed: q(1) succeeds, cut, r(1) succeeds
            "p(2).",  # Should fail: q(2) succeeds, cut, r(2) fails, can't try s(2)
            "p(3).",  # Should succeed: q(3) fails, tries second clause s(3)
        ]
        
        stdout, stderr, returncode = self.run_prolog_commands(commands)
        
        self.assertIn("True", stdout)
        self.assertIn("False", stdout) 
        self.assertIn("True", stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
