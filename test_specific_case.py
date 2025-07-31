#!/usr/bin/env python3

import subprocess
import tempfile
import os

def test_specific_case():
    """Test the specific case that's failing"""
    
    test_dir = tempfile.mkdtemp()
    
    try:
        process = subprocess.Popen(
            ["/usr/bin/python3", "/Users/yuminlee/k-prolog/main.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=test_dir,
        )
        
        commands = [
            "atom_concat(X, world, helloworld).",
            "종료."
        ]
        
        input_text = "\n".join(commands) + "\n"
        
        try:
            stdout, stderr = process.communicate(input=input_text, timeout=10)
            print("STDOUT:")
            print(repr(stdout))
            print("\nFormatted:")
            print(stdout)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            print("Timed out:", repr(stdout))
            
    finally:
        for file in os.listdir(test_dir):
            os.remove(os.path.join(test_dir, file))
        os.rmdir(test_dir)

if __name__ == "__main__":
    test_specific_case()