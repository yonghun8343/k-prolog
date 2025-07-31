#!/usr/bin/env python3

import sys
sys.path.append('.')

from PARSER.parser import parse_string
from PARSER.ast import Struct, Variable
from SOLVER.solver import solve
from UTIL.debug import DebugState
import time

def test_has_factor_direct():
    debug_state = DebugState()
    debug_state.trace_mode = False
    
    print("Testing has_factor Directly")
    print("=" * 30)
    
    program = parse_string(r"""
has_factor(N,L) :- N mod L =:= 0.
has_factor(N,L) :- L * L < N, L2 is L + 2, has_factor(N,L2).
""")
    
    # Test cases where has_factor should succeed
    print("1. Testing has_factor(15,3) - should succeed:")
    query1 = [Struct("has_factor", 2, [Struct("15", 0, []), Struct("3", 0, [])])]
    
    start_time = time.time()
    success1, solutions1 = solve(program, query1, debug_state)
    end_time = time.time()
    
    print(f"   Success: {success1} (Time: {end_time - start_time:.4f}s)")
    
    # Test cases where has_factor should fail 
    print("\n2. Testing has_factor(5,3) - should fail:")
    query2 = [Struct("has_factor", 2, [Struct("5", 0, []), Struct("3", 0, [])])]
    
    start_time = time.time()
    success2, solutions2 = solve(program, query2, debug_state)
    end_time = time.time()
    
    print(f"   Success: {success2} (Time: {end_time - start_time:.4f}s)")
    
    if end_time - start_time > 1.0:
        print("   ❌ has_factor(5,3) taking too long to fail - infinite recursion!")
    else:
        print("   ✅ has_factor(5,3) fails appropriately")
    
    # Test case with larger numbers
    print("\n3. Testing has_factor(7,3) - should fail:")
    query3 = [Struct("has_factor", 2, [Struct("7", 0, []), Struct("3", 0, [])])]
    
    start_time = time.time()
    success3, solutions3 = solve(program, query3, debug_state)
    end_time = time.time()
    
    print(f"   Success: {success3} (Time: {end_time - start_time:.4f}s)")

if __name__ == "__main__":
    test_has_factor_direct()