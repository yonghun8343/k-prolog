#!/usr/bin/env python3

import sys
sys.path.append('.')

from PARSER.parser import parse_string
from PARSER.ast import Struct, Variable
from SOLVER.solver import solve
from UTIL.debug import DebugState
import time

def test_next_prime_fixed():
    debug_state = DebugState()
    debug_state.trace_mode = False
    
    print("Testing next_prime with Fixed is_prime")
    print("=" * 40)
    
    # Test next_prime with the fixed is_prime
    program = parse_string(r"""
is_prime(2).
is_prime(3).
is_prime(P) :- integer(P), P > 3, R is P mod 2, R =\= 0, not(has_factor(P,3)).

has_factor(N,L) :- R is N mod L, R =:= 0.
has_factor(N,L) :- L * L < N, L2 is L + 2, has_factor(N,L2).

next_prime(P,P1) :- P1 is P + 2, is_prime(P1), !.
next_prime(P,P1) :- P2 is P + 2, next_prime(P2,P1).
""")
    
    # Test next_prime from various starting points
    test_cases = [3, 5, 7, 11]
    
    for start in test_cases:
        query = [Struct("next_prime", 2, [Struct(str(start), 0, []), Variable("P")])]
        
        start_time = time.time()
        success, solutions = solve(program, query, debug_state)
        end_time = time.time()
        
        print(f"   next_prime({start}, P): ", end="")
        if success and solutions:
            print(f"P = {solutions[0].get('P')} ({end_time - start_time:.4f}s)")
        else:
            print(f"Failed ({end_time - start_time:.4f}s)")
        
        if end_time - start_time > 2.0:
            print(f"   ❌ next_prime({start}) took too long - stopping tests")
            break

if __name__ == "__main__":
    test_next_prime_fixed()