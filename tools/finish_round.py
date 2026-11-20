# Record what one job built and list the files to pack.
#
# Usage (from the Lean project root):
#   finish_round.py <job list> <out dir> <meta dir> <job id> <twin: true|false>
# Reads <out>/build.log and <out>/metrics.json. Writes into <meta dir>:
#   built.txt     modules of this job that are now compiled
#   failed.txt    modules of this job that had compile errors
#   hashes.tsv    module <tab> sha256 of its .olean <tab> size
#   errors.txt    first error lines for failed modules
#   summary.json  numbers for the round report
#   complete      present only if every module of the job compiled
# and <out>/pack.txt, the files to pack, relative to .lake.
import hashlib, json, os, re, sys

job_file, out, meta, job_id, twin = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5] == "true"
os.makedirs(meta, exist_ok=True)
owned = [m for m in open(job_file, encoding="utf-8").read().split() if m]
owned_set = set(owned)
try:
    log = open(os.path.join(out, "build.log"), encoding="utf-8", errors="replace").read()
except OSError:
    log = ""
try:
    met = json.load(open(os.path.join(out, "metrics.json")))
except (OSError, ValueError):
    met = {"exit_codes": [], "timed_out": False, "wall_s": 0, "cpu_user_s": 0, "cpu_sys_s": 0,
           "max_rss_kb": 0, "chunks": 0, "bookkeeping_deleted": 0}

lib = os.path.join(".lake", "build", "lib", "lean")
ir = os.path.join(".lake", "build", "ir")
built, pack, hashes = [], [], []
for m in owned:
    rel = m.replace(".", os.sep)
    olean = os.path.join(lib, rel + ".olean")
    if not os.path.exists(olean):
        continue
    built.append(m)
    h = hashlib.sha256()
    with open(olean, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    hashes.append("%s\t%s\t%d\n" % (m, h.hexdigest(), os.path.getsize(olean)))
    for base, suffixes in ((lib, (".olean", ".olean.hash", ".ilean", ".ilean.hash", ".trace")), (ir, (".c", ".c.hash"))):
        for s in suffixes:
            p = os.path.join(base, rel + s)
            if os.path.exists(p):
                pack.append(os.path.relpath(p, ".lake"))

# Modules lake reported as failing, over all chunks.
failed = set()
for part in log.split("Some required targets logged failures:")[1:]:
    for line in part.splitlines()[1:]:
        if not line.startswith("- "):
            break
        failed.add(line[2:].strip())
built_set = set(built)
failed_owned = sorted(m for m in failed if m in owned_set and m not in built_set)

# Files compiled here that are not this job's: should be none.
compiled_now = set(re.findall(r"Built (\S+) \(", log))
project_roots = {e[:-5] if e.endswith(".lean") else e for e in os.listdir("src")}
extra = sorted(m for m in compiled_now if m not in owned_set and ":" not in m and m.split(".")[0] in project_roots)

errors = []
if failed_owned:
    path_of = {os.path.join("src", m.replace(".", os.sep) + ".lean"): m for m in failed_owned}
    seen = {}
    for line in log.splitlines():
        mt = re.match(r"error: (src/\S+?\.lean):\d+:\d+: ", line)
        if mt and mt.group(1) in path_of:
            m = path_of[mt.group(1)]
            seen[m] = seen.get(m, 0) + 1
            if seen[m] <= 2 and len(errors) < 200:
                errors.append(line[:300])

open(os.path.join(meta, "built.txt"), "w", encoding="utf-8").write("".join(m + "\n" for m in built))
open(os.path.join(meta, "failed.txt"), "w", encoding="utf-8").write("".join(m + "\n" for m in failed_owned))
open(os.path.join(meta, "hashes.tsv"), "w", encoding="utf-8").write("".join(hashes))
open(os.path.join(meta, "errors.txt"), "w", encoding="utf-8").write("".join(e + "\n" for e in errors))
open(os.path.join(out, "pack.txt"), "w", encoding="utf-8").write("".join(p + "\n" for p in pack))
packed_bytes = sum(os.path.getsize(os.path.join(".lake", p)) for p in pack)
summary = {
    "id": job_id, "twin": twin, "assigned": len(owned), "compiled": len(built), "failed": len(failed_owned),
    "not_reached": len(owned) - len(built) - len(failed_owned), "extra_compiled": len(extra),
    "extra_examples": extra[:3], "timed_out": met["timed_out"], "wall_s": met["wall_s"],
    "cpu_s": met["cpu_user_s"] + met["cpu_sys_s"], "max_rss_kb": met["max_rss_kb"],
    "output_bytes": packed_bytes, "bookkeeping_deleted": met.get("bookkeeping_deleted", 0),
}
try:
    summary["restore"] = open(os.path.join(out, "restore.txt"), encoding="utf-8").read().strip()
except OSError:
    summary["restore"] = ""
json.dump(summary, open(os.path.join(meta, "summary.json"), "w"), indent=1)
if len(built) == len(owned):
    open(os.path.join(meta, "complete"), "w").close()

lines = ["### Job %s%s" % (job_id, " (twin)" if twin else ""), "",
         "| | |", "|---|---|",
         "| Files assigned | %d |" % len(owned),
         "| Compiled | %d |" % len(built),
         "| With errors | %d |" % len(failed_owned),
         "| Not reached | %d%s |" % (summary["not_reached"], " (time limit)" if met["timed_out"] else ""),
         "| Compiled but not assigned here | %d |" % len(extra),
         "| Wall time | %.1f min |" % (met["wall_s"] / 60),
         "| CPU time | %.1f min |" % (summary["cpu_s"] / 60),
         "| Peak memory, one process | %.1f GB |" % (met["max_rss_kb"] / 1e6),
         "| Compiled output | %.1f MB |" % (packed_bytes / 1e6), ""]
if errors:
    lines += ["First errors:", "", "```"] + errors[:20] + ["```", ""]
open(os.path.join(meta, "report.md"), "w", encoding="utf-8").write("\n".join(lines))
print("\n".join(lines))
