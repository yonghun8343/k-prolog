#!/usr/bin/env python3

import sys
sys.path.append('.')

from PARSER.parser import parse_string
from PARSER.ast import Struct, Variable
from SOLVER.solver import solve
from UTIL.debug import DebugState
import time

def test_fixed_is_prime():
    debug_state = DebugState()
    debug_state.trace_mode = False
    
    print("Testing Fixed is_prime Implementation")
    print("=" * 40)
    
    # Test the fixed is_prime
    program = parse_string(r"""
is_prime(2).
is_prime(3).
is_prime(P) :- integer(P), P > 3, R is P mod 2, R =\= 0, not(has_factor(P,3)).

has_factor(N,L) :- R is N mod L, R =:= 0.
has_factor(N,L) :- L * L < N, L2 is L + 2, has_factor(N,L2).
""")
    
    # Test various primes
    test_cases = [2, 3, 5, 7, 11, 4, 6, 8, 9, 10]
    
    for num in test_cases:
        query = [Struct("is_prime", 1, [Struct(str(num), 0, [])])]
        
        start_time = time.time()
        success, solutions = solve(program, query, debug_state)
        end_time = time.time()
        
        expected = num in [2, 3, 5, 7, 11]
        status = "✅" if success == expected else "❌"
        
        print(f"   is_prime({num}): {success} ({end_time - start_time:.4f}s) {status}")
        
        if end_time - start_time > 1.0:
            print(f"   ⚠️  is_prime({num}) took too long!")
            break

if __name__ == "__main__":
    test_fixed_is_prime()