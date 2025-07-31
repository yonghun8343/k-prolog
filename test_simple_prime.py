#!/usr/bin/env python3

import sys
sys.path.append('.')

from PARSER.parser import parse_string
from PARSER.ast import Struct, Variable
from SOLVER.solver import solve
from UTIL.debug import DebugState
import time

def test_simple_prime():
    debug_state = DebugState()
    debug_state.trace_mode = False
    
    print("Testing Simple Prime Cases")
    print("=" * 30)
    
    # Test 1: Just the facts
    print("1. Testing just prime facts:")
    program1 = parse_string("""
is_prime(2).
is_prime(3).
""")
    
    query1 = [Struct("is_prime", 1, [Struct("2", 0, [])])]
    
    start_time = time.time()
    success1, solutions1 = solve(program1, query1, debug_state)
    end_time = time.time()
    
    print(f"   is_prime(2): {success1} ({end_time - start_time:.4f}s)")
    
    # Test 2: Test integer/1 predicate
    print("\n2. Testing integer(5):")
    program2 = parse_string("")
    query2 = [Struct("integer", 1, [Struct("5", 0, [])])]
    
    start_time = time.time()
    success2, solutions2 = solve(program2, query2, debug_state)
    end_time = time.time()
    
    print(f"   integer(5): {success2} ({end_time - start_time:.4f}s)")
    
    # Test 3: Test arithmetic
    print("\n3. Testing P > 3 with P = 5:")
    program3 = parse_string("")
    query3 = [
        Struct("=", 2, [Variable("P"), Struct("5", 0, [])]),
        Struct(">", 2, [Variable("P"), Struct("3", 0, [])])
    ]
    
    start_time = time.time()
    success3, solutions3 = solve(program3, query3, debug_state)
    end_time = time.time()
    
    print(f"   P = 5, P > 3: {success3} ({end_time - start_time:.4f}s)")
    
    # Test 4: Test mod operation
    print("\n4. Testing 5 mod 2:")
    program4 = parse_string("")
    query4 = [
        Struct("mod", 3, [Struct("5", 0, []), Struct("2", 0, []), Variable("R")])
    ]
    
    start_time = time.time()
    success4, solutions4 = solve(program4, query4, debug_state)
    end_time = time.time()
    
    print(f"   5 mod 2 = R: {success4} ({end_time - start_time:.4f}s)")
    if solutions4:
        print(f"   R = {solutions4[0].get('R')}")

if __name__ == "__main__":
    test_simple_prime()