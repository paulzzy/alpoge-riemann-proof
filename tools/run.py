# Run a command with a time limit, copy its output to a log file, and
# record wall time, CPU time of all child processes and peak memory.
import json, os, resource, signal, subprocess, sys, time
limit_s, log_path, metrics_path, cmd = float(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4:]
t0 = time.time()
timed_out = False
with open(log_path, "wb") as log:
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
    def on_alarm(signum, frame):
        global timed_out
        timed_out = True
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    signal.signal(signal.SIGALRM, on_alarm)
    signal.alarm(int(limit_s))
    for line in p.stdout:
        log.write(line)
        sys.stdout.buffer.write(line)
        sys.stdout.buffer.flush()
    code = p.wait()
    signal.alarm(0)
ru = resource.getrusage(resource.RUSAGE_CHILDREN)
json.dump({"exit_code": code, "timed_out": timed_out, "wall_s": time.time() - t0,
           "cpu_user_s": ru.ru_utime, "cpu_sys_s": ru.ru_stime,
           "max_rss_kb": ru.ru_maxrss}, open(metrics_path, "w"))
print("exit code:", code, "| timed out:", timed_out)
