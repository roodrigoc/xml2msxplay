# -*- coding: utf-8 -*-
"""
Merges up to three .bas files line by line.
"""

import sys
import os
import re

if len(sys.argv) < 3:
    print("Usage: python xml2msxplay-merge.py file1.bas file2.bas file3.bas > finalfile.bas")
    sys.exit(1)

files = []
for fname in sys.argv[1:]:
    if not os.path.isfile(fname):
        print(f"file not found: {fname}")
        sys.exit(1)
    with open(fname, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
        files.append(lines)

max_lines = max(len(f) for f in files)

for i in range(max_lines):
    parts = []
    line_number = None
    first_play_found = False

    for f in files:
        if i < len(f):
            line = f[i]
            if " " in line:
                num, code = line.split(" ", 1)
            else:
                num, code = "", line
            if line_number is None and num.isdigit():
                line_number = num

            code_clean = re.sub(r'^\s*PLAY\s*', '', code.strip(), flags=re.IGNORECASE)

            parts.append(code_clean)

    if line_number is None:
        line_number = str((i + 1) * 10)

    print(f"{line_number} PLAY " + ", ".join(parts), end="\r\n")
