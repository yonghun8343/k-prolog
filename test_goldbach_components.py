#!/usr/bin/env python3

import sys
sys.path.append('.')

from PARSER.parser import parse_string
from PARSER.ast import Struct, Variable
from SOLVER.solver import solve
from UTIL.debug import DebugState
import time

def test_goldbach_components():
    debug_state = DebugState()
    debug_state.trace_mode = False
    
    print("Testing Goldbach Components Individually")
    print("=" * 40)
    
    # Test 1: next_prime predicate
    print("1. Testing next_prime(3, P):")
    program1 = parse_string("""
is_prime(2).
is_prime(3).
is_prime(P) :- integer(P), P > 3, P mod 2 =\= 0, not(has_factor(P,3)).

has_factor(N,L) :- N mod L =:= 0.
has_factor(N,L) :- L * L < N, L2 is L + 2, has_factor(N,L2).

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
        
        if end_time - start_time > 2.0:
            print("   ❌ next_prime is still causing infinite recursion")
            return False
        else:
            print("   ✅ next_prime working")
    except Exception as e:
        print(f"   Error: {str(e)[:100]}...")
        return False
    
    # Test 2: Simple goldbach recursive case
    print("\n2. Testing goldbach(6,[P,Q],3) directly:")
    program2 = parse_string("""
is_prime(2).
is_prime(3).
is_prime(P) :- integer(P), P > 3, P mod 2 =\= 0, not(has_factor(P,3)).

has_factor(N,L) :- N mod L =:= 0.
has_factor(N,L) :- L * L < N, L2 is L + 2, has_factor(N,L2).

goldbach(N,[P,Q],P) :- Q is N - P, is_prime(Q), !.
goldbach(N,L,P) :- P < N, next_prime(P,P1), goldbach(N,L,P1).

next_prime(P,P1) :- P1 is P + 2, is_prime(P1), !.
next_prime(P,P1) :- P2 is P + 2, next_prime(P2,P1).
""")
    
    query2 = [Struct("goldbach", 3, [Struct("6", 0, []), Variable("L"), Struct("3", 0, [])])]
    
    start_time = time.time()
    try:
        success2, solutions2 = solve(program2, query2, debug_state)
        end_time = time.time()
        
        print(f"   Success: {success2}")
        if solutions2:
            print(f"   L = {solutions2[0].get('L')}")
        print(f"   Time: {end_time - start_time:.4f}s")
        
        if end_time - start_time > 2.0:
            print("   ❌ goldbach recursive case still problematic")
            return False
        else:
            print("   ✅ goldbach recursive case working")
    except Exception as e:
        print(f"   Error: {str(e)[:100]}...")
        return False
    
    return True

if __name__ == "__main__":
    test_goldbach_components()