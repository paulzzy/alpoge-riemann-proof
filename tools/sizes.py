# Break the build directory down by file type and describe the per-file
# bookkeeping (*.setup.json). Prints markdown.
# Usage: sizes.py <build dir> <expected.txt> <total source MB>  (run from the Lean project root)
import json, os, sys

build, expected_file, total_mb = sys.argv[1], sys.argv[2], float(sys.argv[3])
kinds = [(".setup.json", "bookkeeping (.setup.json)"), (".olean", "compiled (.olean)"), (".ilean", "index (.ilean)"),
         (".trace", "trace"), (".hash", "hashes"), (".c", "C output")]
count, size, setups = {}, {}, []
for root, _, files in os.walk(build):
    for fn in files:
        p = os.path.join(root, fn)
        try:
            b = os.path.getsize(p)
        except OSError:
            continue
        label = "other"
        for suffix, name in kinds:
            if fn.endswith(suffix):
                label = name
                break
        count[label] = count.get(label, 0) + 1
        size[label] = size.get(label, 0) + b
        if label.startswith("bookkeeping"):
            setups.append((p, b))

src_bytes = modules = 0
for m in open(expected_file, encoding="utf-8").read().split():
    try:
        src_bytes += os.path.getsize(os.path.join("src", m.replace(".", os.sep) + ".lean"))
        modules += 1
    except OSError:
        pass

total = sum(size.values())
print("| File type | Files | Total MB | Average KB |")
print("|---|---|---|---|")
for label in sorted(size, key=size.get, reverse=True):
    print("| %s | %d | %.1f | %.1f |" % (label, count[label], size[label] / 1e6, size[label] / count[label] / 1e3))
print("| all | %d | %.1f | |" % (sum(count.values()), total / 1e6))
print()
keep = total - size.get("bookkeeping (.setup.json)", 0)
print("Source for these %d files: %.2f MB. Output without bookkeeping: %.1f MB (%.1f times the source)."
      % (modules, src_bytes / 1e6, keep / 1e6, keep / src_bytes if src_bytes else 0))
if src_bytes:
    print("Scaled by source size to the whole archive (%.1f MB): about %.0f GB without bookkeeping."
          % (total_mb, keep / src_bytes * total_mb / 1e3))
if setups:
    setups.sort(key=lambda x: x[1])
    picks = [setups[0], setups[len(setups) // 2], setups[-1]]
    print()
    print("Bookkeeping files list every imported module:")
    print()
    for p, b in picks:
        try:
            arts = json.load(open(p, encoding="utf-8")).get("importArts", {})
            n = len(arts)
            print("- %.2f MB for %d imports (%.0f bytes per import)" % (b / 1e6, n, b / n if n else 0))
        except (OSError, ValueError):
            print("- %.2f MB (could not parse)" % (b / 1e6))
