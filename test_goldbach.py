#!/usr/bin/env python3

import sys
sys.path.append('.')

from PARSER.parser import parse_string
from PARSER.ast import Struct, Variable
from SOLVER.solver import solve
from UTIL.debug import DebugState
import time

def test_goldbach():
    debug_state = DebugState()
    debug_state.trace_mode = False
    
    print("Testing Goldbach Implementation")
    print("=" * 40)
    
    # Read the program
    with open('/Users/yuminlee/k-prolog/child.pl', 'r') as f:
        program_text = f.read()
    
    try:
        program = parse_string(program_text)
        print(f"Program parsed successfully with {len(program)} clauses")
        
        # Test 1: Base case - goldbach(4, L)
        print("\n1. Testing goldbach(4, L) - base case:")
        query1 = [Struct("goldbach", 2, [Struct("4", 0, []), Variable("L")])]
        
        start_time = time.time()
        success1, solutions1 = solve(program, query1, debug_state)
        end_time = time.time()
        
        print(f"   Success: {success1}")
        print(f"   Solutions: {len(solutions1)}")
        if solutions1:
            print(f"   L = {solutions1[0].get('L')}")
        print(f"   Time: {end_time - start_time:.4f}s")
        
        # Test 2: Small even number - goldbach(6, L)
        print("\n2. Testing goldbach(6, L):")
        query2 = [Struct("goldbach", 2, [Struct("6", 0, []), Variable("L")])]
        
        start_time = time.time()
        success2, solutions2 = solve(program, query2, debug_state)
        end_time = time.time()
        
        print(f"   Success: {success2}")
        print(f"   Solutions: {len(solutions2)}")
        if solutions2:
            print(f"   L = {solutions2[0].get('L')}")
        print(f"   Time: {end_time - start_time:.4f}s")
        
        # Test 3: Slightly larger - goldbach(8, L)
        print("\n3. Testing goldbach(8, L):")
        query3 = [Struct("goldbach", 2, [Struct("8", 0, []), Variable("L")])]
        
        start_time = time.time()
        success3, solutions3 = solve(program, query3, debug_state)
        end_time = time.time()
        
        print(f"   Success: {success3}")
        print(f"   Solutions: {len(solutions3)}")
        if solutions3:
            print(f"   L = {solutions3[0].get('L')}")
        print(f"   Time: {end_time - start_time:.4f}s")
        
        # Test 4: Test helper predicates separately
        print("\n4. Testing is_prime(7):")
        query4 = [Struct("is_prime", 1, [Struct("7", 0, [])])]
        
        start_time = time.time()
        success4, solutions4 = solve(program, query4, debug_state)
        end_time = time.time()
        
        print(f"   Success: {success4}")
        print(f"   Time: {end_time - start_time:.4f}s")
        
        # Test 5: Test next_prime
        print("\n5. Testing next_prime(3, P):")
        query5 = [Struct("next_prime", 2, [Struct("3", 0, []), Variable("P")])]
        
        start_time = time.time()
        success5, solutions5 = solve(program, query5, debug_state)
        end_time = time.time()
        
        print(f"   Success: {success5}")
        print(f"   Solutions: {len(solutions5)}")
        if solutions5:
            print(f"   P = {solutions5[0].get('P')}")
        print(f"   Time: {end_time - start_time:.4f}s")
        
        # Test 6: Medium case with timeout - goldbach(10, L)
        print("\n6. Testing goldbach(10, L) with 5 second timeout:")
        query6 = [Struct("goldbach", 2, [Struct("10", 0, []), Variable("L")])]
        
        start_time = time.time()
        try:
            success6, solutions6 = solve(program, query6, debug_state)
            end_time = time.time()
            
            print(f"   Success: {success6}")
            print(f"   Solutions: {len(solutions6)}")
            if solutions6:
                print(f"   L = {solutions6[0].get('L')}")
            print(f"   Time: {end_time - start_time:.4f}s")
            
            if end_time - start_time > 2.0:
                print("   ⚠️  Taking longer than expected - might indicate a performance issue")
            else:
                print("   ✅ Completed in reasonable time")
                
        except KeyboardInterrupt:
            print("   ⚠️  Interrupted - likely infinite loop or very slow")
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}...")
        
    except Exception as e:
        print(f"Error parsing program: {str(e)[:100]}...")

if __name__ == "__main__":
    test_goldbach()