#!/usr/bin/env python3

import sys
sys.path.append('.')

from PARSER.parser import parse_string
from PARSER.ast import Struct, Variable
from SOLVER.solver import solve
from UTIL.debug import DebugState

def test_prime_list_comprehensive():
    debug_state = DebugState()
    debug_state.trace_mode = False
    
    print("Testing prime_list Comprehensive Cases")
    print("=" * 40)
    
    with open('/Users/yuminlee/k-prolog/child.pl', 'r') as f:
        program_text = f.read()
    
    program = parse_string(program_text)
    
    test_cases = [
        (1, 5, [2, 3, 5]),
        (1, 10, [2, 3, 5, 7]),
        (3, 10, [3, 5, 7]),
        (5, 11, [5, 7, 11])
    ]
    
    for start, end, expected in test_cases:
        print(f"\nTesting prime_list({start}, {end}, L):")
        query = [Struct("prime_list", 3, [Struct(str(start), 0, []), Struct(str(end), 0, []), Variable("L")])]
        
        success, solutions = solve(program, query, debug_state)
        
        if success and solutions:
            result_list = parse_prolog_list(solutions[0]['L'])
            print(f"  Result: {result_list}")
            print(f"  Expected: {expected}")
            
            if result_list == expected:
                print("  ✅ Correct!")
            else:
                print("  ❌ Incorrect result")
        else:
            print("  ❌ Failed to solve")

def parse_prolog_list(prolog_list):
    """Convert Prolog list structure .(a,.(b,[])) to Python list [a,b]"""
    result = []
    current = prolog_list
    
    while hasattr(current, 'name') and current.name == '.' and len(current.params) == 2:
        head = current.params[0]
        tail = current.params[1]
        
        # Convert head to appropriate Python type
        if hasattr(head, 'name') and head.name.isdigit():
            result.append(int(head.name))
        else:
            result.append(str(head))
        
        current = tail
    
    return result

if __name__ == "__main__":
    test_prime_list_comprehensive()