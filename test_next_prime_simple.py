#!/usr/bin/env python3

import sys
sys.path.append('.')

from PARSER.parser import parse_string
from PARSER.ast import Struct, Variable
from SOLVER.solver import solve
from UTIL.debug import DebugState
import time

def test_next_prime_simple():
    debug_state = DebugState()
    debug_state.trace_mode = False
    
    print("Testing next_prime Logic")
    print("=" * 25)
    
    # Test just the recursive structure of next_prime
    print("1. Testing next_prime with simple is_prime facts:")
    program1 = parse_string("""
is_prime(5).
is_prime(7).

next_prime(P,P1) :- P1 is P + 2, is_prime(P1), !.
next_prime(P,P1) :- P2 is P + 2, next_prime(P2,P1).
""")
    
    query1 = [Struct("next_prime", 2, [Struct("3", 0, []), Variable("P")])]
    
    start_time = time.time()
    try:
        success1, solutions1 = solve(program1, query1, debug_state)
        end_time = time.time()
        
        print(f"   Success: {success1}")
        if solutions1:
            print(f"   P = {solutions1[0].get('P')}")
        print(f"   Time: {end_time - start_time:.4f}s")
        
        if end_time - start_time < 0.1:
            print("   ✅ next_prime structure is fine")
        else:
            print("   ❌ next_prime structure has issues")
    except Exception as e:
        print(f"   Error: {str(e)[:100]}...")

if __name__ == "__main__":
    test_next_prime_simple()