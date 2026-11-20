# Build one job's files with a time limit.
#
# Usage (from the Lean project root):
#   build_round.py <job list> <out dir> <time limit in seconds>
# Runs `lake build` on the listed modules in chunks, copies the output to
# <out>/build.log, and writes <out>/metrics.json. While it runs, per-file
# bookkeeping (*.setup.json) older than a minute is deleted to save disk.
import json, os, resource, signal, subprocess, sys, threading, time

job_file, out, limit_s = sys.argv[1], sys.argv[2], float(sys.argv[3])
CHUNK = 1500
mods = [m for m in open(job_file, encoding="utf-8").read().split() if m]
deadline = time.time() + limit_s
t0 = time.time()
stop = threading.Event()
deleted = [0]


def clean():
    root = os.path.join(".lake", "build", "ir")
    while not stop.wait(20):
        cutoff = time.time() - 60
        for d, _, files in os.walk(root):
            for fn in files:
                if fn.endswith(".setup.json"):
                    p = os.path.join(d, fn)
                    try:
                        if os.path.getmtime(p) < cutoff:
                            os.remove(p)
                            deleted[0] += 1
                    except OSError:
                        pass


threading.Thread(target=clean, daemon=True).start()

codes, timed_out, chunks_run = [], False, 0
with open(os.path.join(out, "build.log"), "wb") as log:
    for i in range(0, len(mods), CHUNK):
        left = deadline - time.time()
        if left < 120:
            timed_out = True
            break
        cmd = ["lake", "build"] + ["+" + m for m in mods[i:i + CHUNK]]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
        killed = [False]

        def on_alarm(signum, frame, p=p, killed=killed):
            killed[0] = True
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

        signal.signal(signal.SIGALRM, on_alarm)
        signal.alarm(max(1, int(left)))
        for line in p.stdout:
            log.write(line)
            sys.stdout.buffer.write(line)
            sys.stdout.buffer.flush()
        code = p.wait()
        signal.alarm(0)
        codes.append(code)
        chunks_run += 1
        if killed[0]:
            timed_out = True
            break
stop.set()
ru = resource.getrusage(resource.RUSAGE_CHILDREN)
json.dump({"exit_codes": codes, "timed_out": timed_out, "wall_s": time.time() - t0,
           "cpu_user_s": ru.ru_utime, "cpu_sys_s": ru.ru_stime, "max_rss_kb": ru.ru_maxrss,
           "chunks": chunks_run, "bookkeeping_deleted": deleted[0]},
          open(os.path.join(out, "metrics.json"), "w"))
print("chunks run: %d, exit codes: %s, timed out: %s" % (chunks_run, codes, timed_out))
