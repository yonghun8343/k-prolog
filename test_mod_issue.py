#!/usr/bin/env python3

import sys
sys.path.append('.')

from PARSER.parser import parse_string
from PARSER.ast import Struct, Variable
from SOLVER.solver import solve
from UTIL.debug import DebugState
import time

def test_mod_issue():
    debug_state = DebugState()
    debug_state.trace_mode = False
    
    print("Testing mod Operation Issue")
    print("=" * 30)
    
    # Test 1: Basic mod operation
    print("1. Testing basic mod: 5 mod 2 = R")
    program1 = parse_string("")
    query1 = [Struct("mod", 3, [Struct("5", 0, []), Struct("2", 0, []), Variable("R")])]
    
    start_time = time.time()
    success1, solutions1 = solve(program1, query1, debug_state)
    end_time = time.time()
    
    print(f"   Success: {success1} (Time: {end_time - start_time:.4f}s)")
    if solutions1:
        print(f"   R = {solutions1[0].get('R')}")
    
    # Test 2: Test the mod expression as used in is_prime
    print("\n2. Testing: R is 5 mod 2")
    query2 = [Struct("is", 2, [Variable("R"), Struct("mod", 2, [Struct("5", 0, []), Struct("2", 0, [])])])]
    
    start_time = time.time()
    success2, solutions2 = solve(program1, query2, debug_state)
    end_time = time.time()
    
    print(f"   Success: {success2} (Time: {end_time - start_time:.4f}s)")
    if solutions2:
        print(f"   R = {solutions2[0].get('R')}")
    
    # Test 3: Test the inequality
    print("\n3. Testing: R is 5 mod 2, R =\\= 0")
    query3 = [
        Struct("is", 2, [Variable("R"), Struct("mod", 2, [Struct("5", 0, []), Struct("2", 0, [])])]),
        Struct("=\\=", 2, [Variable("R"), Struct("0", 0, [])])
    ]
    
    start_time = time.time()
    success3, solutions3 = solve(program1, query3, debug_state)
    end_time = time.time()
    
    print(f"   Success: {success3} (Time: {end_time - start_time:.4f}s)")
    if solutions3:
        print(f"   R = {solutions3[0].get('R')}")

if __name__ == "__main__":
    test_mod_issue()