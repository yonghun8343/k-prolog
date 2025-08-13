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
        input_text = "\n".join(commands) + "\n종료."
        try:
            stdout, stderr = process.communicate(input=input_text, timeout=timeout)
            return stdout, stderr, process.returncode
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            return stdout, stderr, -1

    def test_basic_arithmetic_operators(self):
        commands = [
            "_엑스 := 2 + 3.",  # Testing addition, should be 5
            "_와이 := 10 - 4.",  # Testing subtraction, should be 6
            "_지 := 3 * 4.",  # Testing multiplication, should be 12
            "_더블유 := 15 / 3.",  # Testing division, should be 5
            "_에이 := 17 // 5.",  # Testing integer division, should be 3
            "_비 := 17 나머지 5.",  # Testing mod, should be 2
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("_엑스 = 5", stdout)
        self.assertIn("_와이 = 6", stdout)
        self.assertIn("_지 = 12", stdout)
        self.assertIn("_더블유 = 5", stdout)
        self.assertIn("_에이 = 3", stdout)
        self.assertIn("_비 = 2", stdout)

    def test_arithmetic_precedence(self):
        commands = [
            "_엑스 := 2 + 3 * 4.",  # Testing precedence, should be 14, not 20
            "_와이 := 8 / 4 / 2.",  # Testing associativity, should be 1 (left associative)
            "_지 := (2 + 3) * 4.",  # Testing parantheses, should be 20
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("_엑스 = 14", stdout)
        self.assertIn("_와이 = 1", stdout)
        self.assertIn("_지 = 20", stdout)

    def test_comparison_operators(self):
        commands = [
            "5 =:= 2 + 3.",  # Testing =:=, should be True
            "5 =\= 6.",  # Testing =\\=, should be True
            "3 < 5.",  # Testing <, should be True
            "5 > 3.",  # Testing >, should be True
            "5 >= 5.",  # Testing >=, should be True
            "5 =< 5.",  # Testing =<, should be True
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("?- 참\n?- 참\n?- 참\n?- 참\n?- 참\n?- 참\n", stdout)

    def test_unification_operator(self):
        commands = [
            "_엑스 = 5.",  # Testing basic unification
            "_와이 = 안녕.",  # Testing basic unification with constant
            "함수(_에이, _비) = 함수(1, 2).",  # Testing unification with predicates
            "가(나, _씨, 다(라, _에프, 마(바, 사, _제이))) = 가(_비, 차, 다(_이, 아프, 마(_에이치, 사, 자))).",  # Testing complex unification with nested predicates
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("_엑스 = 5", stdout)
        self.assertIn("_와이 = 안녕", stdout)
        self.assertIn("_에이 = 1", stdout)
        self.assertIn("_비 = 2", stdout)
        self.assertIn("_씨 = 차", stdout)
        self.assertIn("_에프 = 아프", stdout)
        self.assertIn("_제이 = 자", stdout)
        self.assertIn("_비 = 나", stdout)
        self.assertIn("_이 = 라", stdout)
        self.assertIn("_에이치 = 바", stdout)

    def test_nested_expressions(self):
        commands = [
            "_엑스 := (2 + 3) * (4 - 1).",  # Should be 15
            "_와이 := 2 + (3 * (4 + 1)).",  # Should be 17
            "_지 := ((8 / 4) + 1) * 3.",  # Should be 9
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("_엑스 = 15", stdout)
        self.assertIn("_와이 = 17", stdout)
        self.assertIn("_지 = 9", stdout)

    def test_anonymous_variables(self):
        content = """
        테스트_익명(_엑스, _) :- _엑스 := 3.
        테스트_익명2(_, _와이) :- _와이 = 4.
        테스트_매치(_, _).
        """

        self.create_test_file("익명.pl", content)
        commands = [
            "[익명].",
            "테스트_익명(_엘, 5).",
            "테스트_익명(_에이, _비).",
            "테스트_익명2(3, 4).",
            "테스트_익명2(4, 5).",
            "테스트_매치(푸, 바).",
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("익명.pl에서 적재했습니다", stdout)

        self.assertIn("_엘 = 3", stdout)
        self.assertIn("_에이 = 3", stdout)
        self.assertIn("참", stdout)
        self.assertIn("거짓", stdout)
        self.assertIn("참", stdout)

    def test_not(self):
        content = """
        빨강(사과).
        파랑(_엑스) :- not(빨강(_엑스)).
        """

        self.create_test_file("부정.pl", content)

        commands = [
            "[부정].",
            "파랑(사과).",
            "not(15 =:= (2 + 3) * (4 - 1)).",
            "not(3 =:= 1 + 3).",
            "not(_엑스 := 4).",
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("부정.pl에서 적재했습니다", stdout)
        self.assertIn("거짓", stdout)
        self.assertIn("거짓", stdout)
        self.assertIn("참", stdout)
        self.assertIn("거짓", stdout)

    def test_n_queens(self):
        content = """
        퀸들(_엔,_큐에스) :- 범위(1,_엔,_엔에스), 순열(_엔에스,_큐에스), 안전(_큐에스).

        안전([]).
        안전([_큐|_큐에스]) :- 안전(_큐에스), not(공격(_큐,_큐에스)).

        공격(_엑스,_엑스에스) :- 공격(_엑스,1,_엑스에스).
        공격(_엑스,_엔,[_와이|_]) :- _엑스 := _와이+_엔; _엑스 := _와이-_엔.
        공격(_엑스,_엔,[_|_와이에스]) :- _엔1 := _엔+1, 공격(_엑스,_엔1,_와이에스).

        범위(_엔,_엔,[_엔]).
        범위(_엠,_엔,[_엠|_엔에스]) :- _엠 < _엔, _엠1 := _엠+1, 범위(_엠1,_엔,_엔에스).
        """

        self.create_test_file("엔퀸.pl", content)

        commands = [
            "[엔퀸].",
            "퀸들(4, _큐에스).",
            ";",
            ";",
            # "퀸들(6, _큐에스).",  # takes too long
            # ";",
            # ";",
            # ";",
            # ";",
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("엔퀸.pl에서 적재했습니다", stdout)
        self.assertIn("_큐에스 = [2, 4, 1, 3]", stdout)
        self.assertIn("_큐에스 = [3, 1, 4, 2]", stdout)
        # self.assertIn("_큐에스 = [2, 4, 6, 1, 3, 5]", stdout)
        # self.assertIn("_큐에스 = [3, 6, 2, 5, 1, 4]", stdout)
        # self.assertIn("_큐에스 = [4, 1, 5, 2, 6, 3]", stdout)
        # self.assertIn("_큐에스 = [5, 3, 1, 6, 4, 2]", stdout)

    def test_operator_orders(self):
        commands = [
            "_엑스 := +(2,3).",
            "_와이 := +(*(2, 3), 4 + 1).",
            "_지 := /(+(6, 4), 나머지(7, 3)).",
            "_에이 := +(+(1, 2), *(/(8, 4), 3)).",
            "_비 := *(+(2, 3), (4 + 나머지(10, 3))).",
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("_엑스 = 5", stdout)
        self.assertIn("_와이 = 11", stdout)
        self.assertIn("_지 = 10", stdout)
        self.assertIn("_에이 = 9", stdout)
        self.assertIn("_비 = 25", stdout)

    def test_cut_operator(self):
        content = """최대값(_엑스, _와이, _엑스) :- _엑스 >= _와이, !.
                최대값(_엑스, _와이, _와이).

                첫번째([_머리|_], _머리) :- !.
                첫번째([_|_꼬리], _엑스) :- 첫번째(_꼬리, _엑스).

                선택1(가) :- !.
                선택1(나).
                선택1(다).

                테스트_컷(1) :- !, fail.
                테스트_컷(2).

                멤버_컷(_엑스, [_엑스|_]) :- !.
                멤버_컷(_엑스, [_|_꼬리]) :- 멤버_컷(_엑스, _꼬리)."""

        self.create_test_file("컷_테스트.pl", content)

        # Should only give one answer
        commands1 = [
            "[컷_테스트].",
            "최대값(5, 3, _지).",
        ]
        stdout1, stderr1, returncode1 = self.run_prolog_commands(commands1)
        self.assertIn("_지 = 5", stdout1)

        # Should not show multiple solutions due to cut
        commands2 = ["[컷_테스트].", "최대값(2, 7, _지)."]
        stdout2, stderr2, returncode2 = self.run_prolog_commands(commands2)
        self.assertIn("_지 = 7", stdout2)

        commands3 = [
            "[컷_테스트].",
            "선택1(_엑스).",
            ";",
            ";",
            ";",  # Should only give X = a due to cut
        ]
        stdout3, stderr3, returncode3 = self.run_prolog_commands(commands3)
        self.assertIn("_엑스 = 가", stdout3)
        self.assertNotIn("_엑스 = 나", stdout3)  # Cut should prevent this
        self.assertNotIn("_엑스 = 다", stdout3)  # Cut should prevent this

    def test_cut_with_backtracking(self):
        content = """피(_엑스) :- 큐(_엑스), !, 알(_엑스).
                    피(_엑스) :- 에스(_엑스).

                    큐(1).
                    큐(2).
                    알(1).
                    에스(3)."""

        self.create_test_file("백트랙_테스트.pl", content)

        commands = [
            "[백트랙_테스트].",
            "피(1).",  # Should succeed: q(1) succeeds, cut, r(1) succeeds
            "피(2).",  # Should fail: q(2) succeeds, cut, r(2) fails, can't try s(2)
            "피(3).",  # Should succeed: q(3) fails, tries second clause s(3)
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("참", stdout)
        self.assertIn("거짓", stdout)
        self.assertIn("참", stdout)

    # TODO these are not in the english version
    def test_arrow_if_then_only(self):
        content = """
        양수인지(_엑스) :- _엑스 > 0 -> 쓰기('양수입니다').
        음수인지(_엑스) :- _엑스 < 0 -> 쓰기('음수입니다').
        """

        self.create_test_file("조건부.pl", content)

        commands = [
            "[조건부].",
            "양수인지(5).",  # Should succeed and write '양수입니다'
            "양수인지(-3).",  # Should fail (condition false, no else)
            "음수인지(-2).",  # Should succeed and write '음수입니다'
            "음수인지(4).",  # Should fail (condition false, no else)
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("조건부.pl에서 적재했습니다", stdout)
        self.assertIn("양수입니다", stdout)
        self.assertIn("음수입니다", stdout)
        self.assertIn("참", stdout)  # For successful cases
        self.assertIn("거짓", stdout)  # For failed cases

    def test_arrow_if_then_else(self):
        content = """
        절댓값(_엑스, _결과) :- (_엑스 >= 0 -> _결과 = _엑스 ; _결과 := -1 * _엑스).
        최대값(_에이, _비, _최대) :- (_에이 >= _비 -> _최대 = _에이 ; _최대 = _비).
        """

        self.create_test_file("조건문.pl", content)

        commands = [
            "[조건문].",
            "절댓값(5, _결과1).",  # Should give _결과1 = 5
            "절댓값(-3, _결과2).",  # Should give _결과2 = 3
            "최대값(7, 4, _최대1).",  # Should give _최대1 = 7
            "최대값(2, 8, _최대2).",  # Should give _최대2 = 8
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn("조건문.pl에서 적재했습니다", stdout)
        self.assertIn("_결과1 = 5", stdout)
        self.assertIn("_결과2 = 3", stdout)
        self.assertIn("_최대1 = 7", stdout)
        self.assertIn("_최대2 = 8", stdout)

    def test_char_code(self):
        commands = [
            "문자코드(a, _코드).",  # Testing char_code with lowercase letter
            "문자코드('A', _코드2).",  # Testing char_code with uppercase letter
            "문자코드('0', _코드3).",  # Testing char_code with digit
            "문자코드(' ', _코드4).",  # Testing char_code with space
            "문자코드('가', _코드5).",  # Testing char_code with Korean character
            "문자코드(_문자, 97).",  # Testing char_code with code to char (97 = 'a')
            "문자코드(_문자2, 65).",  # Testing char_code with code to char (65 = 'A')
            "문자코드(_문자3, 48).",  # Testing char_code with code to char (48 = '0')
            "문자코드('a', 97).",  # Testing char_code verification (should succeed)
            "문자코드('a', 98).",  # Testing char_code wrong verification (should fail)
            "문자코드('!', _코드6).",  # Testing char_code with special character
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn(
            "참", stdout
        )  # Should have multiple 참 for successful conversions
        self.assertIn("거짓", stdout)  # Should have 거짓 for wrong verification
        self.assertIn("_코드 = 97", stdout)  # ASCII code for 'a'
        self.assertIn("_코드2 = 65", stdout)  # ASCII code for 'A'
        self.assertIn("_코드3 = 48", stdout)  # ASCII code for '0'
        self.assertIn("_코드4 = 32", stdout)  # ASCII code for space
        self.assertIn("_문자 = a", stdout)  # Character for code 97
        self.assertIn("_문자2 = A", stdout)  # Character for code 65
        self.assertIn("_문자3 = 0", stdout)  # Character for code 48
        self.assertIn("_코드6 = 33", stdout)  # ASCII code for '!'

    def test_atom_chars(self):
        commands = [
            "문자리스트(abc, _문자들).",  # Testing atom_chars with simple atom
            "문자리스트(123, _숫자들).",  # Testing atom_chars with number atom
            "문자리스트('hello', _헬로).",  # Testing atom_chars with quoted atom
            "문자리스트('', _빈문자열).",  # Testing atom_chars with empty atom
            "문자리스트(안녕, _한글).",  # Testing atom_chars with Korean atom
            "문자리스트(_원자, ['a', 'b', 'c']).",  # Testing atom_chars from chars to atom
            "문자리스트(_원자2, ['1', '2', '3']).",  # Testing atom_chars from number chars to atom
            "문자리스트(_원자3, []).",  # Testing atom_chars from empty list to atom
            "문자리스트(hello, ['h', 'e', 'l', 'l', 'o']).",  # Testing atom_chars verification (should succeed)
            "문자리스트(hello, ['h', 'i']).",  # Testing atom_chars wrong verification (should fail)
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        self.assertIn(
            "참", stdout
        )  # Should have multiple 참 for successful conversions
        self.assertIn("거짓", stdout)  # Should have 거짓 for wrong verification
        self.assertIn("_문자들 = ['a', 'b', 'c']", stdout)  # Characters for 'abc'
        self.assertIn("_숫자들 = ['1', '2', '3']", stdout)  # Characters for '123'
        self.assertIn(
            "_헬로 = ['h', 'e', 'l', 'l', 'o']", stdout
        )  # Characters for 'hello'
        self.assertIn("_빈문자열 = []", stdout)  # Empty list for empty atom
        self.assertIn("_한글 = ['안', '녕']", stdout)  # Characters for Korean '안녕'
        self.assertIn("_원자 = abc", stdout)  # Atom from chars ['a', 'b', 'c']
        self.assertIn("_원자2 = 123", stdout)  # Atom from chars ['1', '2', '3']
        self.assertIn("_원자3 = ''", stdout)  # Empty atom from empty list

    def test_record_family(self):
        content = """
        테스트_기록(T1, T2, R1, R2) :-
            레코드기록(foo, hello(world), R1),
            레코드기록(foo, goodbye(world), R2),
            레코드(foo, T1, R1),
            레코드(foo, T2, R2).

        테스트_지우기(R) :-
            지우기(R).

        테스트_지우기_다음(T, R) :-
            레코드(foo, T, R).
        """
        self.create_test_file("record_family.pl", content)

        commands = [
            "[record_family].",
            "테스트_기록(T1, T2, R1, R2).",
            "테스트_지우기(R1).",
            "테스트_지우기_다음(T, R).",
        ]

        stdout, stderr, returncode = self.run_prolog_commands(commands)

        # Check that recording succeeded and references returned
        self.assertIn("T1 = hello(world)", stdout)
        self.assertIn("T2 = goodbye(world)", stdout)
        self.assertIn("R1 =", stdout)  # some opaque reference struct, e.g. $ref(...)
        self.assertIn("R2 =", stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
