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
    
    print("Testing Goldbach Components")
    print("=" * 40)
    
    # Test just the prime checking parts first
    program_text = """
is_prime(2).
is_prime(3).
is_prime(P) :- integer(P), P > 3, P mod 2 =\= 0, not(has_factor(P,3)).

has_factor(N,L) :- N mod L =:= 0.
has_factor(N,L) :- L * L < N, L2 is L + 2, has_factor(N,L2).
"""
    
    try:
        program = parse_string(program_text)
        print(f"Prime checking program parsed with {len(program)} clauses")
        
        # Test 1: Basic prime checks
        print("\n1. Testing basic prime checks:")
        for num in [2, 3, 5, 7, 11, 4, 6, 8, 9]:
            query = [Struct("is_prime", 1, [Struct(str(num), 0, [])])]
            
            start_time = time.time()
            success, solutions = solve(program, query, debug_state)
            end_time = time.time()
            
            print(f"   is_prime({num}): {success} ({end_time - start_time:.4f}s)")
            
            if end_time - start_time > 0.5:
                print(f"   ⚠️  is_prime({num}) took {end_time - start_time:.4f}s - might be a problem")
                break
        
        # Test 2: has_factor predicate specifically
        print("\n2. Testing has_factor(15, 3):")
        query2 = [Struct("has_factor", 2, [Struct("15", 0, []), Struct("3", 0, [])])]
        
        start_time = time.time()
        success2, solutions2 = solve(program, query2, debug_state)
        end_time = time.time()
        
        print(f"   Success: {success2}")
        print(f"   Time: {end_time - start_time:.4f}s")
        
        # Test 3: has_factor with larger numbers
        print("\n3. Testing has_factor(21, 7):")
        query3 = [Struct("has_factor", 2, [Struct("21", 0, []), Struct("7", 0, [])])]
        
        start_time = time.time()
        success3, solutions3 = solve(program, query3, debug_state)
        end_time = time.time()
        
        print(f"   Success: {success3}")
        print(f"   Time: {end_time - start_time:.4f}s")
        
    except Exception as e:
        print(f"Error: {str(e)[:100]}...")

def test_next_prime():
    debug_state = DebugState()
    debug_state.trace_mode = False
    
    print("\n" + "=" * 40)
    print("Testing next_prime predicate")
    
    program_text = """
is_prime(2).
is_prime(3).
is_prime(P) :- integer(P), P > 3, P mod 2 =\= 0, not(has_factor(P,3)).

has_factor(N,L) :- N mod L =:= 0.
has_factor(N,L) :- L * L < N, L2 is L + 2, has_factor(N,L2).

next_prime(P,P1) :- P1 is P + 2, is_prime(P1), !.
next_prime(P,P1) :- P2 is P + 2, next_prime(P2,P1).
"""
    
    try:
        program = parse_string(program_text)
        print(f"next_prime program parsed with {len(program)} clauses")
        
        # Test next_prime with small numbers
        print("\n1. Testing next_prime(3, P):")
        query1 = [Struct("next_prime", 2, [Struct("3", 0, []), Variable("P")])]
        
        start_time = time.time()
        success1, solutions1 = solve(program, query1, debug_state)
        end_time = time.time()
        
        print(f"   Success: {success1}")
        if solutions1:
            print(f"   P = {solutions1[0].get('P')}")
        print(f"   Time: {end_time - start_time:.4f}s")
        
        if end_time - start_time > 1.0:
            print("   ⚠️  next_prime is taking too long - likely infinite recursion")
        else:
            print("   ✅ next_prime working normally")
            
    except Exception as e:
        print(f"Error: {str(e)[:100]}...")

if __name__ == "__main__":
    test_goldbach_components()
    test_next_prime()