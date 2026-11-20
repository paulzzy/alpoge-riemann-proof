# Choose what to build. Writes targets.txt (arguments for `lake build`)
# and expected.txt (modules that should end up compiled).
import os, random, re, sys
kind, lib, n, seed, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
src = "src"
imp_re = re.compile(r"^\s*(?:(?:public|private)\s+)?(?:meta\s+)?import\s+(?:all\s+)?(.*)$")
skip = {"all", "public", "private", "meta", "runtime"}

def header_imports(path):
    imps, depth = [], 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            if depth:
                depth = max(0, depth + s.count("/-") - s.count("-/"))
                continue
            if not s or s.startswith("--") or s in ("module", "prelude"):
                continue
            if s.startswith("/-"):
                depth = max(0, s.count("/-") - s.count("-/"))
                continue
            m = imp_re.match(line)
            if not m:
                break
            rest = m.group(1).split("--")[0].replace("import", " ")
            imps.extend(t for t in rest.split() if t not in skip)
    return imps

mods = {}
for root, _, files in os.walk(src):
    for fn in files:
        if fn.endswith(".lean"):
            p = os.path.join(root, fn)
            mods[os.path.relpath(p, src)[:-5].replace(os.sep, ".")] = p
proj = {m: [i for i in header_imports(p) if i in mods] for m, p in mods.items()}

if kind == "lib":
    roots = [m for m in mods if m.startswith(lib + ".")]
    if not roots:
        sys.exit("no modules under " + lib)
    seen, stack = set(), list(roots)
    while stack:
        m = stack.pop()
        if m not in seen:
            seen.add(m)
            stack.extend(proj[m])
    targets, expected = [lib], sorted(seen)
else:
    leaves = sorted(m for m, deps in proj.items() if not deps)
    expected = sorted(random.Random(seed).sample(leaves, min(n, len(leaves))))
    targets = ["+" + m for m in expected]
    print("files that import only Mathlib:", len(leaves))

# Names go to lake as separate arguments, one per line of targets.txt.
bad = [m for m in expected if m.startswith("-") or re.search(r"\s", m) or not m.isprintable()]
if bad:
    sys.exit("unexpected module names: " + repr(bad[:5]))
open(os.path.join(out, "targets.txt"), "w").write("\n".join(targets) + "\n")
open(os.path.join(out, "expected.txt"), "w").write("\n".join(expected) + "\n")
print("project modules:", len(mods), "| expected to build:", len(expected))
