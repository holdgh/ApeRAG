# Test file with lint errors
import os
import sys
import json  # unused import

def bad_function( ):  # bad spacing
    x=1+2  # no spaces around operators
    print(f"hello world")  # f-string without placeholders
    return x 