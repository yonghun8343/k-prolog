#!/usr/bin/env python3

import sys
sys.path.append('.')

from PARSER.parser import parse_string
from PARSER.ast import Struct, Variable
from SOLVER.solver import solve
from UTIL.debug import DebugState
import time

def test_negation_fix():
    debug_state = DebugState()
    debug_state.trace_mode = False
    
    print("Testing Negation + Constraint Delay Fix")
    print("=" * 40)
    
    # Test 1: Simple negation with arithmetic - should handle constraints properly
    print("1. Testing not(X > 5) with X unbound:")
    program1 = parse_string("")
    query1 = [Struct("not", 1, [Struct(">", 2, [Variable("X"), Struct("5", 0, [])])])]
    
    start_time = time.time()
    try:
        success1, solutions1 = solve(program1, query1, debug_state)
        end_time = time.time()
        
        print(f"   Success: {success1}")
        print(f"   Solutions: {len(solutions1)}")
        print(f"   Time: {end_time - start_time:.4f}s")
        
        if end_time - start_time < 1.0:
            print("   ✅ Negation with unbound arithmetic handled properly")
        else:
            print("   ⚠️  Still taking too long")
    except Exception as e:
        print(f"   Error: {str(e)[:100]}...")
    
    # Test 2: Test has_factor predicate specifically
    print("\n2. Testing has_factor(15, 3) - should succeed quickly:")
    program2 = parse_string("""
has_factor(N,L) :- N mod L =:= 0.
has_factor(N,L) :- L * L < N, L2 is L + 2, has_factor(N,L2).
""")
    query2 = [Struct("has_factor", 2, [Struct("15", 0, []), Struct("3", 0, [])])]
    
    start_time = time.time()
    try:
        success2, solutions2 = solve(program2, query2, debug_state)
        end_time = time.time()
        
        print(f"   Success: {success2}")
        print(f"   Time: {end_time - start_time:.4f}s")
        
        if success2 and end_time - start_time < 0.1:
            print("   ✅ has_factor working correctly")
        else:
            print("   ❌ has_factor still has issues")
    except Exception as e:
        print(f"   Error: {str(e)[:100]}...")
    
    # Test 3: Test negation of has_factor
    print("\n3. Testing not(has_factor(7, 3)) - should succeed (7 has no factor 3):")
    program3 = parse_string("""
has_factor(N,L) :- N mod L =:= 0.
has_factor(N,L) :- L * L < N, L2 is L + 2, has_factor(N,L2).
""")
    query3 = [Struct("not", 1, [Struct("has_factor", 2, [Struct("7", 0, []), Struct("3", 0, [])])])]
    
    start_time = time.time()
    try:
        success3, solutions3 = solve(program3, query3, debug_state)
        end_time = time.time()
        
        print(f"   Success: {success3}")
        print(f"   Time: {end_time - start_time:.4f}s")
        
        if success3 and end_time - start_time < 1.0:
            print("   ✅ Negation of has_factor working correctly")
        else:
            print("   ❌ Negation of has_factor still has issues")
    except Exception as e:
        print(f"   Error: {str(e)[:100]}...")
    
    # Test 4: Simple is_prime test
    print("\n4. Testing is_prime(7) with fixed negation:")
    program4 = parse_string("""
is_prime(2).
is_prime(3).
is_prime(P) :- integer(P), P > 3, P mod 2 =\= 0, not(has_factor(P,3)).

has_factor(N,L) :- N mod L =:= 0.
has_factor(N,L) :- L * L < N, L2 is L + 2, has_factor(N,L2).
""")
    query4 = [Struct("is_prime", 1, [Struct("7", 0, [])])]
    
    start_time = time.time()
    try:
        success4, solutions4 = solve(program4, query4, debug_state)
        end_time = time.time()
        
        print(f"   Success: {success4}")
        print(f"   Time: {end_time - start_time:.4f}s")
        
        if success4 and end_time - start_time < 2.0:
            print("   ✅ is_prime(7) working with fixed negation!")
        else:
            print("   ❌ is_prime still has issues")
    except Exception as e:
        print(f"   Error: {str(e)[:100]}...")

if __name__ == "__main__":
    test_negation_fix()