# Record the results of one round and write its report.
#
# Runs in a job that never executes archive code. Everything read from the
# build jobs' artifacts is treated as untrusted text.
#
# Usage: collect.py <plan dir> <metas dir> <state dir> <run id> <report file>
#   <plan dir>   plan.json and job-XX.txt from the plan job
#   <metas dir>  one sub-directory per meta artifact (meta-rN-jXX[-twin])
#   <state dir>  the `state` folder of the probe-results branch (updated in place)
# Writes built / left / round to $GITHUB_OUTPUT when that is set.
import json, os, re, sys

plan_dir, metas, state, run_id, report_file = sys.argv[1:6]
if not run_id.isdigit():
    sys.exit("bad run id")
plan = json.load(open(os.path.join(plan_dir, "plan.json")))
rnd = int(plan["round"])
total = int(plan["total"])


def read_names(path, allowed):
    try:
        text = open(path, encoding="utf-8", errors="replace").read(50_000_000)
    except OSError:
        return []
    return [m for m in text.split() if m in allowed]


def read_summary(d):
    try:
        s = json.load(open(os.path.join(d, "summary.json")))
    except (OSError, ValueError):
        return None
    out = {}
    for k in ("assigned", "compiled", "failed", "not_reached", "extra_compiled", "max_rss_kb", "output_bytes"):
        v = s.get(k, 0)
        out[k] = int(v) if isinstance(v, (int, float)) else 0
    for k in ("wall_s", "cpu_s"):
        v = s.get(k, 0)
        out[k] = float(v) if isinstance(v, (int, float)) else 0.0
    out["timed_out"] = s.get("timed_out") is True
    return out


def read_hashes(d, allowed):
    h = {}
    try:
        for line in open(os.path.join(d, "hashes.tsv"), encoding="utf-8", errors="replace"):
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2 and parts[0] in allowed and re.fullmatch(r"[0-9a-f]{64}", parts[1]):
                h[parts[0]] = parts[1]
    except OSError:
        pass
    return h


os.makedirs(os.path.join(state, "built"), exist_ok=True)
rows, all_built, all_failed, errors = [], [], [], []
data_jobs = []
twin_note = "No twin job result."
for job in plan["jobs"]:
    jid = job["id"]
    if not re.fullmatch(r"\d{2,3}", jid):
        sys.exit("bad job id in plan")
    owned = [m for m in open(os.path.join(plan_dir, "job-%s.txt" % jid), encoding="utf-8").read().split() if m]
    allowed = set(owned)
    d = os.path.join(metas, "meta-r%d-j%s" % (rnd, jid))
    s = read_summary(d) if os.path.isdir(d) else None
    stored = os.path.exists(os.path.join(d, "data_ok"))
    built = read_names(os.path.join(d, "built.txt"), allowed) if s else []
    failed = read_names(os.path.join(d, "failed.txt"), allowed) if s else []
    if s is None:
        rows.append("| %s | %d | no result | | | | | | |" % (jid, len(owned)))
        continue
    if built and stored:
        open(os.path.join(state, "built", "r%02d-j%s.txt" % (rnd, jid)), "w", encoding="utf-8").write("".join(m + "\n" for m in built))
        all_built += built
        data_jobs.append(jid)
    all_failed += failed
    try:
        for line in open(os.path.join(d, "errors.txt"), encoding="utf-8", errors="replace").read(200_000).splitlines()[:6]:
            errors.append(line[:300].replace("`", "'"))
    except OSError:
        pass
    per_file = s["cpu_s"] / s["compiled"] if s["compiled"] else 0
    rows.append("| %s | %d | %d%s | %d | %d%s | %d | %.0f min | %.1f s | %.1f GB |" % (
        jid, len(owned), len(built), "" if stored or not built else " (not stored)", len(failed),
        s["not_reached"], " (time limit)" if s["timed_out"] else "", s["extra_compiled"],
        s["wall_s"] / 60, per_file, s["max_rss_kb"] / 1e6))

    if jid == plan.get("twin_of"):
        td = os.path.join(metas, "meta-r%d-j%s-twin" % (rnd, jid))
        if os.path.isdir(td):
            a, b = read_hashes(d, allowed), read_hashes(td, allowed)
            both = sorted(set(a) & set(b))
            diff = [m for m in both if a[m] != b[m]]
            twin_note = ("Job %s was built twice on separate runners: %d files compared, %d byte-identical, %d different."
                         % (jid, len(both), len(both) - len(diff), len(diff)))
            if diff:
                twin_note += " Different, for example: " + ", ".join("`%s`" % m for m in diff[:5])

# State: what is built, what failed, and where this round's files are stored.
if all_failed:
    path = os.path.join(state, "failed.txt")
    known = set(open(path, encoding="utf-8").read().split()) if os.path.exists(path) else set()
    open(path, "w", encoding="utf-8").write("".join(m + "\n" for m in sorted(known | set(all_failed))))
if all_built:
    with open(os.path.join(state, "rounds.tsv"), "a", encoding="utf-8") as f:
        f.write("%d\t%s\tstate-r%d\n" % (rnd, run_id, rnd))
open(os.path.join(state, "data-jobs-r%d.txt" % rnd), "w").write("".join(j + "\n" for j in data_jobs))

built_total = plan["built_before"] + len(all_built)
left = total - built_total
L = ["# Build round %d" % rnd, "",
     "| | |", "|---|---|",
     "| Files in the archive | %d |" % total,
     "| Compiled before this round | %d |" % plan["built_before"],
     "| Scheduled this round | %d in %d jobs |" % (plan["scheduled"], len(plan["jobs"])),
     "| Compiled this round | %d |" % len(all_built),
     "| With compile errors this round | %d |" % len(set(all_failed)),
     "| Compiled so far | %d (%.1f%%) |" % (built_total, 100.0 * built_total / total),
     "| Still to build | %d |" % left, "",
     twin_note, "",
     "| Job | Assigned | Compiled | Errors | Not reached | Compiled but not assigned | Wall | CPU per file | Peak memory |",
     "|---|---|---|---|---|---|---|---|---|"] + rows + [""]
if all_failed:
    L += ["Files with compile errors (first 50):", ""] + ["- `%s`" % m for m in sorted(set(all_failed))[:50]] + [""]
if errors:
    L += ["First error lines:", "", "```"] + errors[:40] + ["```", ""]
text = "\n".join(L)
open(report_file, "w", encoding="utf-8").write(text)
print(text)
gh_out = os.environ.get("GITHUB_OUTPUT")
if gh_out:
    with open(gh_out, "a") as f:
        f.write("built=%d\nleft=%d\nround=%d\n" % (len(all_built), left, rnd))
