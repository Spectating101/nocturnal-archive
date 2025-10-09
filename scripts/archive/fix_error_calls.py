#!/usr/bin/env python3
"""
Fix create_problem_response calls in finance_kpis.py
"""

import re

# Read the file
with open('nocturnal-archive-api/src/routes/finance_kpis.py', 'r') as f:
    content = f.read()

# Pattern to match create_problem_response calls with 5 arguments
pattern = r'create_problem_response\(\s*request,\s*(\d+),\s*"([^"]+)",\s*"([^"]+)",\s*([^)]+)\)'

def replace_func(match):
    status = match.group(1)
    code = match.group(2)
    title = match.group(3)
    detail = match.group(4)
    return f'create_problem_response(\n                {detail},\n                {status},\n                "{code}"\n            )'

# Replace all occurrences
new_content = re.sub(pattern, replace_func, content)

# Write back to file
with open('nocturnal-archive-api/src/routes/finance_kpis.py', 'w') as f:
    f.write(new_content)

print("Fixed create_problem_response calls")