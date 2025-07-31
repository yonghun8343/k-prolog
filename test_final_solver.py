#!/usr/bin/env python3

import sys
sys.path.append('.')

from PARSER.parser import parse_string
from PARSER.ast import Struct, Variable
from SOLVER.solver import solve
from UTIL.debug import DebugState
import time

def test_final_solver():
    debug_state = DebugState()
    debug_state.trace_mode = False
    
    print("Testing Final Solver Implementation")
    print("=" * 50)
    
    # Test 1: Basic facts
    print("1. Testing basic facts:")
    program1 = parse_string("""
likes(mary, food).
likes(john, food).
""")
    query1 = [Struct("likes", 2, [Variable("X"), Struct("food", 0, [])])]
    
    start_time = time.time()
    success1, solutions1 = solve(program1, query1, debug_state)
    end_time = time.time()
    
    print(f"   Success: {success1}")
    print(f"   Solutions: {len(solutions1)} - {[s.get('X') for s in solutions1]}")
    print(f"   Time: {end_time - start_time:.4f}s")
    
    if success1 and len(solutions1) == 2:
        print("   ✅ Basic facts work correctly")
    else:
        print("   ❌ Basic facts failed")
    
    # Test 2: Simple cut
    print("\n2. Testing cut functionality:")
    program2 = parse_string("""
test(a) :- !.
test(b).
test(c).
""")
    query2 = [Struct("test", 1, [Variable("X")])]
    
    start_time = time.time()
    success2, solutions2 = solve(program2, query2, debug_state)
    end_time = time.time()
    
    print(f"   Success: {success2}")
    print(f"   Solutions: {len(solutions2)} - {[s.get('X') for s in solutions2]}")
    print(f"   Time: {end_time - start_time:.4f}s")
    
    if success2 and len(solutions2) == 1 and solutions2[0].get('X').__str__() == 'a':
        print("   ✅ Cut works correctly")
    else:
        print("   ❌ Cut failed")
    
    # Test 3: Constraint delay
    print("\n3. Testing constraint delay:")
    program3 = parse_string("""
test_delay(X) :- X > 3, X = 5.
""")
    query3 = [Struct("test_delay", 1, [Variable("X")])]
    
    start_time = time.time()
    success3, solutions3 = solve(program3, query3, debug_state)
    end_time = time.time()
    
    print(f"   Success: {success3}")
    print(f"   Solutions: {len(solutions3)}")
    if solutions3:
        print(f"   X = {solutions3[0].get('X')}")
    print(f"   Time: {end_time - start_time:.4f}s")
    
    if success3 and solutions3 and str(solutions3[0].get('X')) == '5':
        print("   ✅ Constraint delay works correctly")
    else:
        print("   ❌ Constraint delay failed")
    
    # Test 4: N-Queens (small case)
    print("\n4. Testing N-Queens (4x4):")
    try:
        with open('nqueens.pl', 'r') as f:
            nqueens_text = f.read()
        
        nqueens_program = parse_string(nqueens_text)
        nqueens_query = [Struct("queens", 2, [Struct("4", 0, []), Variable("Qs")])]
        
        start_time = time.time()
        success4, solutions4 = solve(nqueens_program, nqueens_query, debug_state)
        end_time = time.time()
        
        print(f"   Success: {success4}")
        print(f"   Solutions: {len(solutions4)}")
        print(f"   Time: {end_time - start_time:.4f}s")
        
        if success4 and len(solutions4) > 0:
            print("   ✅ N-Queens works without recursion issues!")
        else:
            print("   ❌ N-Queens failed")
            
    except Exception as e:
        print(f"   N-Queens error: {str(e)[:100]}...")
    
    # Test 5: Prime factorization with constraint delay
    print("\n5. Testing prime factorization with constraint delay:")
    try:
        with open('child.pl', 'r') as f:
            prime_text = f.read()
        
        prime_program = parse_string(prime_text)
        prime_query = [Struct("prime_factors_mult", 2, [Struct("12", 0, []), Variable("L")])]
        
        start_time = time.time()
        success5, solutions5 = solve(prime_program, prime_query, debug_state)
        end_time = time.time()
        
        print(f"   Success: {success5}")
        print(f"   Solutions: {len(solutions5)}")
        if solutions5:
            print(f"   L = {solutions5[0].get('L')}")
        print(f"   Time: {end_time - start_time:.4f}s")
        
        if success5 and solutions5:
            print("   ✅ Prime factorization with constraint delay works!")
        else:
            print("   ❌ Prime factorization failed")
            
    except Exception as e:
        print(f"   Prime factorization error: {str(e)[:100]}...")
    
    print("\n" + "=" * 50)
    print("Final solver testing complete!")

if __name__ == "__main__":
    test_final_solver()