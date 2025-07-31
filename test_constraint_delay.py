#!/usr/bin/env python3

import sys
sys.path.append('.')

from PARSER.parser import parse_string
from PARSER.ast import Struct, Variable
from SOLVER.solver import solve
from UTIL.debug import DebugState

def test_constraint_delay():
    debug_state = DebugState()
    debug_state.trace_mode = False
    
    print("Testing constraint delay mechanism")
    print("=" * 40)
    
    # Test 1: Simple uninstantiated constraint - should fail
    print("1. Testing X > 3 with unbound X (should fail):")
    program1 = parse_string("")  # Empty program
    query1 = [Struct(">", 2, [Variable("X"), Struct("3", 0, [])])]
    
    try:
        success1, solutions1 = solve(program1, query1, debug_state)
        print(f"   Success: {success1}")
        print(f"   Solutions: {len(solutions1)}")
        if success1:
            print("   ❌ This should have failed!")
        else:
            print("   ✅ Correctly failed with instantiation error")
    except Exception as e:
        print(f"   Error (expected): {str(e)[:100]}...")
    
    # Test 2: Constraint that can be delayed and then satisfied
    print("\n2. Testing constraint delay that succeeds:")
    program2 = parse_string("""
test(X) :- X > 3, X = 5.
""")
    query2 = [Struct("test", 1, [Variable("X")])]
    
    try:
        success2, solutions2 = solve(program2, query2, debug_state)
        print(f"   Success: {success2}")
        print(f"   Solutions: {len(solutions2)}")
        if success2 and len(solutions2) == 1:
            print(f"   X = {solutions2[0].get('X')}")
            print("   ✅ Constraint delay worked correctly!")
        else:
            print("   ❌ Should have found X = 5")
    except Exception as e:
        print(f"   Error: {str(e)[:100]}...")
    
    # Test 3: Test the original prime_factors_mult case
    print("\n3. Testing prime_factors_mult(315, L):")
    with open('/Users/yuminlee/k-prolog/child.pl', 'r') as f:
        program_text = f.read()
    
    program3 = parse_string(program_text)
    query3 = [Struct("prime_factors_mult", 2, [Struct("315", 0, []), Variable("L")])]
    
    try:
        success3, solutions3 = solve(program3, query3, debug_state)
        print(f"   Success: {success3}")
        print(f"   Solutions: {len(solutions3)}")
        if success3 and solutions3:
            print(f"   L = {solutions3[0].get('L')}")
            print("   ✅ Prime factorization worked!")
        else:
            print("   ❌ Prime factorization failed")
    except Exception as e:
        print(f"   Error: {str(e)[:100]}...")

if __name__ == "__main__":
    test_constraint_delay()