# Check one build step and print rows for the checks table.
# Usage: check.py <label> <build.log> <metrics.json> <expected.txt> <base.txt or ->
# (run from the Lean project root). Exit code 1 if any check fails.
import json, os, re, sys

label, log_file, metrics_file, expected_file, base_file = sys.argv[1:6]
log = open(log_file, encoding="utf-8", errors="replace").read()
expected = open(expected_file, encoding="utf-8").read().split()
base = set(open(base_file, encoding="utf-8").read().split()) if base_file != "-" else set()
try:
    met = json.load(open(metrics_file))
except (OSError, ValueError):
    met = {"exit_code": None, "timed_out": False, "wall_s": 0, "cpu_user_s": 0, "cpu_sys_s": 0, "max_rss_kb": 0}

compiled = [m for m in expected
            if os.path.exists(os.path.join(".lake", "build", "lib", "lean", m.replace(".", os.sep) + ".olean"))]
built_now = set(re.findall(r"Built (\S+) \(", log))
again = sorted(built_now & base)
errors = []
tail = log.split("Some required targets logged failures:")
if len(tail) > 1:
    errors = [ln[2:].strip() for ln in tail[-1].splitlines() if ln.startswith("- ")]

ok = True
def row(check, passed, detail):
    global ok
    ok = ok and passed
    print("| %s | %s | %s |" % (check, "PASS" if passed else "FAIL", detail.replace("|", "/")))

cpu = met["cpu_user_s"] + met["cpu_sys_s"]
row(label + ": files compiled", len(compiled) == len(expected) and met["exit_code"] == 0,
    "%d of %d, exit code %s%s, wall %.1f min, CPU %.1f min, peak memory of one process %.1f GB"
    % (len(compiled), len(expected), met["exit_code"], " (time limit)" if met["timed_out"] else "",
       met["wall_s"] / 60, cpu / 60, met["max_rss_kb"] / 1e6))
if errors:
    row(label + ": files with errors", False, ", ".join("`%s`" % e for e in errors[:8]) + (" ..." if len(errors) > 8 else ""))
if base:
    row(label + ": already-built files compiled again", not again,
        "%d of %d%s" % (len(again), len(base), (" e.g. `%s`" % again[0]) if again else ""))
sys.exit(0 if ok else 1)
