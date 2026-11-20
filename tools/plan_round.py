# Plan one round of the split build.
#
# Every file is compiled exactly once: within a round, a job may only build a
# file if all of that file's not-yet-built imports are built by the same job in
# the same round. Files whose imports are spread over several jobs wait for a
# later round.
#
# Usage (from the Lean project root):
#   plan_round.py --state <dir> --jobs <n> --cap <n> --out <dir>
# <dir>/state holds what earlier rounds recorded:
#   rounds.tsv        round <tab> run id <tab> artifact name
#   built/*.txt       module names compiled so far
#   failed.txt        module names that failed to compile
# Writes job-XX.txt (modules in build order) and plan.json to --out, and
# round / scheduled / matrix to $GITHUB_OUTPUT when that is set.
import argparse, collections, glob, json, os, re, sys

ap = argparse.ArgumentParser()
ap.add_argument("--state", required=True)
ap.add_argument("--jobs", type=int, required=True)
ap.add_argument("--cap", type=int, required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--twin-size", type=int, default=1500)
ap.add_argument("--key-depth", type=int, default=3)
args = ap.parse_args()
if not (1 <= args.jobs <= 200 and 1 <= args.cap <= 20000):
    sys.exit("jobs must be 1-200 and cap 1-20000")

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
names = sorted(mods)
bad = [m for m in names if m.startswith("-") or re.search(r"\s", m) or not m.isprintable()]
if bad:
    sys.exit("unexpected module names: " + repr(bad[:5]))
idx = {m: i for i, m in enumerate(names)}
n = len(names)
deps = [[idx[i] for i in header_imports(mods[m]) if i in idx] for m in names]
rev = [[] for _ in range(n)]
for u in range(n):
    for v in deps[u]:
        rev[v].append(u)

# What earlier rounds recorded.
built = bytearray(n)
for path in sorted(glob.glob(os.path.join(args.state, "built", "*.txt"))):
    for m in open(path, encoding="utf-8").read().split():
        if m in idx:
            built[idx[m]] = 1
failed_known = []
fpath = os.path.join(args.state, "failed.txt")
if os.path.exists(fpath):
    failed_known = sorted({m for m in open(fpath, encoding="utf-8").read().split() if m in idx})
prior, last_round = [], 0
rpath = os.path.join(args.state, "rounds.tsv")
if os.path.exists(rpath):
    for line in open(rpath, encoding="utf-8"):
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 3 and parts[0].isdigit() and parts[1].isdigit() and re.fullmatch(r"[A-Za-z0-9_.-]+", parts[2]):
            prior.append({"round": int(parts[0]), "run_id": parts[1], "name": parts[2]})
            last_round = max(last_round, int(parts[0]))
this_round = last_round + 1

# Files that failed, and everything that imports them, cannot be built.
blocked = bytearray(n)
stack = [idx[m] for m in failed_known if not built[idx[m]]]
for u in stack:
    blocked[u] = 1
while stack:
    u = stack.pop()
    for w in rev[u]:
        if not blocked[w] and not built[w]:
            blocked[w] = 1
            stack.append(w)

# Use no more jobs than the remaining files need: with fewer jobs, fewer files
# have their imports split across jobs, so more can be built in the round.
C = args.cap
todo = sum(1 for u in range(n) if not built[u] and not blocked[u])
J = max(1, min(args.jobs, -(-todo // C)))

# One pass in dependency order. A file with no unbuilt imports starts in the
# job that holds its directory; other files follow their imports.
key = [".".join(m.split(".")[: args.key_depth]) for m in names]
indeg = [0] * n
queue = collections.deque()
for u in range(n):
    if built[u] or blocked[u]:
        continue
    c = sum(1 for v in deps[u] if not built[v])
    indeg[u] = c
    if c == 0:
        queue.append(u)
job = [-1] * n
load = [0] * J
keyjob = {}
lists = [[] for _ in range(J)]
while queue:
    u = queue.popleft()
    unbuilt = [v for v in deps[u] if not built[v]]
    j = -1
    if not unbuilt:
        j = keyjob.get(key[u], -1)
        if j < 0 or load[j] >= C:
            j = min(range(J), key=load.__getitem__)
            keyjob[key[u]] = j
        if load[j] >= C:
            j = -1
    else:
        owners = {job[v] for v in unbuilt}
        if len(owners) == 1:
            j = owners.pop()
            if j >= 0 and load[j] >= C:
                j = -1
    if j >= 0:
        job[u] = j
        load[j] += 1
        lists[j].append(names[u])
    for w in rev[u]:
        if built[w] or blocked[w]:
            continue
        indeg[w] -= 1
        if indeg[w] == 0:
            queue.append(w)

# Self-check: each job's list is closed under unbuilt imports and in build order.
for j, lst in enumerate(lists):
    seen = set()
    for m in lst:
        for v in deps[idx[m]]:
            if not built[v] and names[v] not in seen:
                sys.exit("plan error: %s scheduled before its import %s" % (m, names[v]))
        seen.add(m)

os.makedirs(args.out, exist_ok=True)
active = [(j, lst) for j, lst in enumerate(lists) if lst]
jobs = []
for new_id, (j, lst) in enumerate(active):
    jid = "%02d" % new_id
    open(os.path.join(args.out, "job-%s.txt" % jid), "w", encoding="utf-8").write("".join(m + "\n" for m in lst))
    jobs.append({"id": jid, "files": len(lst)})

# One job is built twice so the two results can be compared byte for byte.
twin_of = None
if jobs:
    candidates = [x for x in jobs if x["files"] >= 200] or jobs
    twin_of = min(candidates, key=lambda x: abs(x["files"] - args.twin_size))["id"]

scheduled = sum(x["files"] for x in jobs)
n_built = sum(built)
plan = {
    "round": this_round, "total": n, "built_before": n_built, "blocked": sum(blocked),
    "failed_known": len(failed_known), "scheduled": scheduled,
    "left_after": n - n_built - sum(blocked) - scheduled,
    "jobs": jobs, "twin_of": twin_of, "prior": prior, "cap": C,
}
json.dump(plan, open(os.path.join(args.out, "plan.json"), "w"), indent=1)

include = [{"id": x["id"], "twin": False} for x in jobs]
if twin_of is not None:
    include.append({"id": twin_of, "twin": True})
gh_out = os.environ.get("GITHUB_OUTPUT")
if gh_out:
    with open(gh_out, "a") as f:
        f.write("round=%d\n" % this_round)
        f.write("scheduled=%d\n" % scheduled)
        f.write("matrix=%s\n" % json.dumps({"include": include}))
print("round %d: %d files total, %d built before, %d blocked by failures" % (this_round, n, n_built, sum(blocked)))
print("scheduled %d files in %d jobs (largest %d, smallest %d); %d left for later rounds"
      % (scheduled, len(jobs), max([x["files"] for x in jobs] or [0]), min([x["files"] for x in jobs] or [0]), plan["left_after"]))
print("twin of job:", twin_of)
