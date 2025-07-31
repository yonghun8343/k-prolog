#!/usr/bin/env python3

import sys
sys.path.append('.')

from PARSER.parser import parse_string
from PARSER.ast import Struct, Variable
from SOLVER.solver import solve
from UTIL.debug import DebugState
import time

def test_complex_prime():
    debug_state = DebugState()
    debug_state.trace_mode = False
    
    print("Testing Complex is_prime Implementation")
    print("=" * 40)
    
    # Test the complex is_prime with has_factor
    print("1. Testing is_prime(5) with complex definition:")
    program1 = parse_string(r"""
is_prime(2).
is_prime(3).
is_prime(P) :- integer(P), P > 3, P mod 2 =\= 0, not(has_factor(P,3)).

has_factor(N,L) :- N mod L =:= 0.
has_factor(N,L) :- L * L < N, L2 is L + 2, has_factor(N,L2).
""")
    
    query1 = [Struct("is_prime", 1, [Struct("5", 0, [])])]
    
    start_time = time.time()
    try:
        success1, solutions1 = solve(program1, query1, debug_state)
        end_time = time.time()
        
        print(f"   Success: {success1}")
        print(f"   Time: {end_time - start_time:.4f}s")
        
        if end_time - start_time < 2.0:
            print("   ✅ Complex is_prime working")
        else:
            print("   ❌ Complex is_prime still slow/infinite")
            return
    except Exception as e:
        print(f"   Error: {str(e)[:100]}...")
        return
    
    # Test next_prime with complex is_prime
    print("\n2. Testing next_prime(3,P) with complex is_prime:")
    query2 = [Struct("next_prime", 2, [Struct("3", 0, []), Variable("P")])]
    
    program2 = parse_string(r"""
is_prime(2).
is_prime(3).
is_prime(P) :- integer(P), P > 3, P mod 2 =\= 0, not(has_factor(P,3)).

has_factor(N,L) :- N mod L =:= 0.
has_factor(N,L) :- L * L < N, L2 is L + 2, has_factor(N,L2).

next_prime(P,P1) :- P1 is P + 2, is_prime(P1), !.
next_prime(P,P1) :- P2 is P + 2, next_prime(P2,P1).
""")
    
    start_time = time.time()
    try:
        success2, solutions2 = solve(program2, query2, debug_state)
        end_time = time.time()
        
        print(f"   Success: {success2}")
        if solutions2:
            print(f"   P = {solutions2[0].get('P')}")
        print(f"   Time: {end_time - start_time:.4f}s")
        
        if end_time - start_time < 2.0:
            print("   ✅ next_prime with complex is_prime working")
        else:
            print("   ❌ next_prime with complex is_prime still has issues")
    except Exception as e:
        print(f"   Error: {str(e)[:100]}...")

if __name__ == "__main__":
    test_complex_prime()