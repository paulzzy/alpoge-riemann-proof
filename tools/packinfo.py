# Describe a packed checkpoint in one line.
# Usage: packinfo.py <raw bytes> <packed bytes> <total source MB> <expected.txt>
# (run from the Lean project root)
import os, sys

raw, packed, total_mb, expected_file = int(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
mods = open(expected_file, encoding="utf-8").read().split()
src = 0
for m in mods:
    try:
        src += os.path.getsize(os.path.join("src", m.replace(".", os.sep) + ".lean"))
    except OSError:
        pass
line = "%d files: %.1f MB unpacked, %.1f MB packed" % (len(mods), raw / 1e6, packed / 1e6)
if src:
    line += "; scaled by source size to the whole archive: about %.1f GB packed" % (packed / src * total_mb / 1e3)
print(line)
