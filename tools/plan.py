# Choose files to build on top of an existing checkpoint: files that import at
# least one project file and whose project imports are all already built.
# Usage: plan.py <base.txt> <count> <out dir>   (run from the Lean project root)
# Writes targets_a.txt / targets_b.txt (arguments for `lake build`, two halves
# in build order) and expected_a.txt / expected_b.txt (module names).
import os, re, sys

base_file, n, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
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

base = set(open(base_file, encoding="utf-8").read().split())
missing = [m for m in base if m not in mods]
if missing:
    sys.exit("checkpoint lists unknown modules: " + repr(missing[:5]))

built, targets, layers = set(base), [], 0
while len(targets) < n:
    layer = sorted(m for m in mods if m not in built and proj[m] and all(d in built for d in proj[m]))
    if not layer:
        break
    layers += 1
    take = layer[: n - len(targets)]
    targets += take
    built |= set(take)

bad = [m for m in targets if m.startswith("-") or re.search(r"\s", m) or not m.isprintable()]
if bad:
    sys.exit("unexpected module names: " + repr(bad[:5]))
half = (len(targets) + 1) // 2
for name, part in (("a", targets[:half]), ("b", targets[half:])):
    open(os.path.join(out, "targets_%s.txt" % name), "w", encoding="utf-8").write("".join("+" + m + "\n" for m in part))
    open(os.path.join(out, "expected_%s.txt" % name), "w", encoding="utf-8").write("".join(m + "\n" for m in part))
print("already built:", len(base), "| chosen on top:", len(targets), "from", layers, "layer(s)")
