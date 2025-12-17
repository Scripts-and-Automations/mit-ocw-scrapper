#!/usr/bin/env python3
import os
import re

# pasta com os PDFs
DIR = "."

# regex para capturar algo como "_lec0.3", "_lec5.1", "_lec10.2"
pat = re.compile(r"_lec(\d{1,2}\.\d)", re.IGNORECASE)

for old in os.listdir(DIR):
    if not old.lower().endswith(".pdf"):
        continue

    m = pat.search(old)
    if not m:
        print(f"Ignorando {old!r}: não é '*_lecNN.D.pdf'")
        continue

    num_str = m.group(1)  # ex: "0.3", "5.1", "10.2"
    new = f"Klute - Lecture {num_str}.pdf"

    src = os.path.join(DIR, old)
    dst = os.path.join(DIR, new)
    if os.path.exists(dst):
        print(f"Pular   {old!r} → {new!r} (já existe)")
    else:
        print(f"{old!r} → {new!r}")
        os.rename(src, dst)