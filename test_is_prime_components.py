#!/usr/bin/env python3

import sys
sys.path.append('.')

from PARSER.parser import parse_string
from PARSER.ast import Struct, Variable
from SOLVER.solver import solve
from UTIL.debug import DebugState
import time

def test_is_prime_components():
    debug_state = DebugState()
    debug_state.trace_mode = False
    
    print("Testing is_prime Components")
    print("=" * 30)
    
    # Test 1: Just the conditions without negation
    print("1. Testing: integer(5), 5 > 3, 5 mod 2 =\\= 0")
    program1 = parse_string("")
    query1 = [
        Struct("integer", 1, [Struct("5", 0, [])]),
        Struct(">", 2, [Struct("5", 0, []), Struct("3", 0, [])]),
        Struct("=\\=", 2, [Struct("mod", 3, [Struct("5", 0, []), Struct("2", 0, []), Variable("_")]), Struct("0", 0, [])])
    ]
    
    start_time = time.time()
    success1, solutions1 = solve(program1, query1, debug_state)
    end_time = time.time()
    
    print(f"   Success: {success1} (Time: {end_time - start_time:.4f}s)")
    
    # Test 2: Add the negation
    print("\n2. Testing: integer(5), 5 > 3, 5 mod 2 =\\= 0, not(has_factor(5,3))")
    program2 = parse_string(r"""
has_factor(N,L) :- N mod L =:= 0.
has_factor(N,L) :- L * L < N, L2 is L + 2, has_factor(N,L2).
""")
    
    query2 = [
        Struct("integer", 1, [Struct("5", 0, [])]),
        Struct(">", 2, [Struct("5", 0, []), Struct("3", 0, [])]),
        Struct("=\\=", 2, [Struct("mod", 3, [Struct("5", 0, []), Struct("2", 0, []), Variable("_")]), Struct("0", 0, [])]),
        Struct("not", 1, [Struct("has_factor", 2, [Struct("5", 0, []), Struct("3", 0, [])])])
    ]
    
    start_time = time.time()
    success2, solutions2 = solve(program2, query2, debug_state)
    end_time = time.time()
    
    print(f"   Success: {success2} (Time: {end_time - start_time:.4f}s)")
    
    if end_time - start_time > 1.0:
        print("   ❌ Adding negation causes slowdown!")
    else:
        print("   ✅ All components work together")
    
    # Test 3: Test the full is_prime(5) clause directly
    print("\n3. Testing full is_prime(5) clause:")
    program3 = parse_string(r"""
has_factor(N,L) :- N mod L =:= 0.
has_factor(N,L) :- L * L < N, L2 is L + 2, has_factor(N,L2).
""")
    
    # Manually expand is_prime(5) clause
    query3 = [
        Struct("integer", 1, [Struct("5", 0, [])]),
        Struct(">", 2, [Struct("5", 0, []), Struct("3", 0, [])]),
        Struct("=\\=", 2, [Struct("mod", 3, [Struct("5", 0, []), Struct("2", 0, []), Variable("R")]), Struct("0", 0, [])]),
        Struct("not", 1, [Struct("has_factor", 2, [Struct("5", 0, []), Struct("3", 0, [])])])
    ]
    
    start_time = time.time()
    success3, solutions3 = solve(program3, query3, debug_state)
    end_time = time.time()
    
    print(f"   Success: {success3} (Time: {end_time - start_time:.4f}s)")

if __name__ == "__main__":
    test_is_prime_components()