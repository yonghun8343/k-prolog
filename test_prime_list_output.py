#!/usr/bin/env python3

import sys
sys.path.append('.')

from PARSER.parser import parse_string
from PARSER.ast import Struct, Variable
from SOLVER.solver import solve
from UTIL.debug import DebugState

def test_prime_list_output():
    debug_state = DebugState()
    debug_state.trace_mode = False
    
    print("Testing prime_list Output Variable Substitution")
    print("=" * 50)
    
    # Read the prime_list program
    with open('/Users/yuminlee/k-prolog/child.pl', 'r') as f:
        program_text = f.read()
    
    program = parse_string(program_text)
    
    # Test prime_list(1, 5, L)
    print("Testing prime_list(1, 5, L):")
    query = [Struct("prime_list", 3, [Struct("1", 0, []), Struct("5", 0, []), Variable("L")])]
    
    success, solutions = solve(program, query, debug_state)
    
    print(f"Success: {success}")
    print(f"Number of solutions: {len(solutions)}")
    
    if solutions:
        for i, solution in enumerate(solutions):
            print(f"Solution {i + 1}:")
            for var, value in solution.items():
                print(f"  {var} = {value}")
                print(f"  {var} type: {type(value)}")
                
                # If it's a complex structure, let's examine it more closely
                if hasattr(value, 'name'):
                    print(f"  {var} structure: name={value.name}, arity={value.arity}")
                    if hasattr(value, 'params'):
                        print(f"  {var} params: {value.params}")
    
    # Let's also test a simpler case
    print("\n" + "=" * 50)
    print("Testing simpler case: p_list(2, 5, L):")
    query2 = [Struct("p_list", 3, [Struct("2", 0, []), Struct("5", 0, []), Variable("L")])]
    
    success2, solutions2 = solve(program, query2, debug_state)
    
    print(f"Success: {success2}")
    if solutions2:
        for i, solution in enumerate(solutions2):
            print(f"Solution {i + 1}:")
            for var, value in solution.items():
                print(f"  {var} = {value}")

if __name__ == "__main__":
    test_prime_list_output()