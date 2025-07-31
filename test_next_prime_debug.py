#!/usr/bin/env python3

import sys
sys.path.append('.')

from PARSER.parser import parse_string
from PARSER.ast import Struct, Variable
from SOLVER.solver import solve
from UTIL.debug import DebugState
import time

def test_next_prime_debug():
    debug_state = DebugState()
    debug_state.trace_mode = False
    
    print("Debugging next_prime Logic")
    print("=" * 30)
    
    # First, test the individual steps of next_prime(3, P1)
    program = parse_string(r"""
is_prime(2).
is_prime(3).
is_prime(P) :- integer(P), P > 3, R is P mod 2, R =\= 0, not(has_factor(P,3)).

has_factor(N,L) :- R is N mod L, R =:= 0.
has_factor(N,L) :- L * L < N, L2 is L + 2, has_factor(N,L2).
""")
    
    # Step 1: Test P1 is 3 + 2
    print("1. Testing: P1 is 3 + 2")
    query1 = [Struct("is", 2, [Variable("P1"), Struct("+", 2, [Struct("3", 0, []), Struct("2", 0, [])])])]
    
    start_time = time.time()
    success1, solutions1 = solve(program, query1, debug_state)
    end_time = time.time()
    
    print(f"   Success: {success1}, P1 = {solutions1[0].get('P1') if solutions1 else 'None'} ({end_time - start_time:.4f}s)")
    
    # Step 2: Test is_prime(5)
    print("\n2. Testing: is_prime(5)")
    query2 = [Struct("is_prime", 1, [Struct("5", 0, [])])]
    
    start_time = time.time()
    success2, solutions2 = solve(program, query2, debug_state)
    end_time = time.time()
    
    print(f"   Success: {success2} ({end_time - start_time:.4f}s)")
    
    # Step 3: Test the first clause of next_prime directly
    print("\n3. Testing: P1 is 3 + 2, is_prime(P1)")
    query3 = [
        Struct("is", 2, [Variable("P1"), Struct("+", 2, [Struct("3", 0, []), Struct("2", 0, [])])]),
        Struct("is_prime", 1, [Variable("P1")])
    ]
    
    start_time = time.time()
    success3, solutions3 = solve(program, query3, debug_state)
    end_time = time.time()
    
    print(f"   Success: {success3}, P1 = {solutions3[0].get('P1') if solutions3 else 'None'} ({end_time - start_time:.4f}s)")
    
    # Step 4: Test next_prime with cut removed to see what happens
    print("\n4. Testing next_prime without cut:")
    program_no_cut = parse_string(r"""
is_prime(2).
is_prime(3).
is_prime(P) :- integer(P), P > 3, R is P mod 2, R =\= 0, not(has_factor(P,3)).

has_factor(N,L) :- R is N mod L, R =:= 0.
has_factor(N,L) :- L * L < N, L2 is L + 2, has_factor(N,L2).

next_prime(P,P1) :- P1 is P + 2, is_prime(P1).
""")
    
    query4 = [Struct("next_prime", 2, [Struct("3", 0, []), Variable("P")])]
    
    start_time = time.time()
    success4, solutions4 = solve(program_no_cut, query4, debug_state)
    end_time = time.time()
    
    print(f"   Success: {success4}, P = {solutions4[0].get('P') if solutions4 else 'None'} ({end_time - start_time:.4f}s)")

if __name__ == "__main__":
    test_next_prime_debug()