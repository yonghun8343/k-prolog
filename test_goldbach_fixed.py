#!/usr/bin/env python3

import sys
sys.path.append('.')

from PARSER.parser import parse_string
from PARSER.ast import Struct, Variable
from SOLVER.solver import solve
from UTIL.debug import DebugState
import time

def test_goldbach_fixed():
    debug_state = DebugState()
    debug_state.trace_mode = False
    
    print("Testing Goldbach Problem with Fixed Negation")
    print("=" * 45)
    
    # Read the fixed program
    with open('/Users/yuminlee/k-prolog/child.pl', 'r') as f:
        program_text = f.read()
    
    try:
        program = parse_string(program_text)
        print(f"Goldbach program parsed with {len(program)} clauses")
        
        # Test 1: goldbach(4, L) - base case
        print("\n1. Testing goldbach(4, L):")
        query1 = [Struct("goldbach", 2, [Struct("4", 0, []), Variable("L")])]
        
        start_time = time.time()
        success1, solutions1 = solve(program, query1, debug_state)
        end_time = time.time()
        
        print(f"   Success: {success1}")
        if solutions1:
            print(f"   L = {solutions1[0].get('L')}")
        print(f"   Time: {end_time - start_time:.4f}s")
        
        # Test 2: goldbach(6, L)
        print("\n2. Testing goldbach(6, L):")
        query2 = [Struct("goldbach", 2, [Struct("6", 0, []), Variable("L")])]
        
        start_time = time.time()
        success2, solutions2 = solve(program, query2, debug_state)
        end_time = time.time()
        
        print(f"   Success: {success2}")
        if solutions2:
            print(f"   L = {solutions2[0].get('L')}")
        print(f"   Time: {end_time - start_time:.4f}s")
        
        # Test 3: goldbach(8, L)
        print("\n3. Testing goldbach(8, L):")
        query3 = [Struct("goldbach", 2, [Struct("8", 0, []), Variable("L")])]
        
        start_time = time.time()
        success3, solutions3 = solve(program, query3, debug_state)
        end_time = time.time()
        
        print(f"   Success: {success3}")
        if solutions3:
            print(f"   L = {solutions3[0].get('L')}")
        print(f"   Time: {end_time - start_time:.4f}s")
        
        # Test 4: goldbach(10, L) 
        print("\n4. Testing goldbach(10, L):")
        query4 = [Struct("goldbach", 2, [Struct("10", 0, []), Variable("L")])]
        
        start_time = time.time()
        success4, solutions4 = solve(program, query4, debug_state)
        end_time = time.time()
        
        print(f"   Success: {success4}")
        if solutions4:
            print(f"   L = {solutions4[0].get('L')}")
        print(f"   Time: {end_time - start_time:.4f}s")
        
        if end_time - start_time < 5.0:
            print("   ✅ Goldbach working efficiently!")
        else:
            print("   ⚠️  Still slow, may need more optimization")
        
        # Summary
        print(f"\n{'=' * 45}")
        if all([success1, success2, success3, success4]):
            print("🎉 ALL GOLDBACH TESTS PASSED!")
            print("The negation + constraint delay fix resolved the infinite loop bug!")
        else:
            print("Some tests failed - may need additional fixes")
            
    except Exception as e:
        print(f"Error: {str(e)[:100]}...")

if __name__ == "__main__":
    test_goldbach_fixed()