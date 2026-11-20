# Checkpoint probe run 1

Run: https://github.com/paulzzy/alpoge-riemann-proof/actions/runs/44777512441
Job results: build and pack = success; restore and build on top = success

## Job 1: build a slice and pack it

```
runner: 4 cores, 15 GB RAM, 95G free disk
lean: Lean (version 4.33.1, x86_64-unknown-linux-gnu, commit 819816b2e0a3bf405af45ae5c7af2491d8f5bee6, Release)
mathlib: 0df444a360eaa60ab8c11dca51a86af692955474 (clean checkout, prebuilt cache complete)
archive sha256: 9631b4f020199e580ba86178cb56c6e9b09f690c2369a80dc4334aa93f49c7fc
```

| Check | Result | Detail |
|---|---|---|
| Slice: files compiled | PASS | 836 of 836, exit code 0, wall 23.3 min, CPU 89.1 min, peak memory of one process 9.6 GB |
| Slice still counts as built after deleting the bookkeeping | PASS | nothing needed rebuilding |
| Checkpoint packed | INFO | 836 files: 402.8 MB unpacked, 112.7 MB packed; scaled by source size to the whole archive: about 21.4 GB packed |

Build output by file type:

| File type | Files | Total MB | Average KB |
|---|---|---|---|
| bookkeeping (.setup.json) | 836 | 6383.8 | 7636.2 |
| compiled (.olean) | 836 | 373.2 | 446.4 |
| index (.ilean) | 836 | 20.4 | 24.4 |
| C output | 836 | 5.3 | 6.4 |
| trace | 836 | 3.9 | 4.7 |
| hashes | 2508 | 0.0 | 0.0 |
| all | 6688 | 6786.7 | |

Source for these 836 files: 5.43 MB. Output without bookkeeping: 402.8 MB (74.2 times the source).
Scaled by source size to the whole archive (1030.5 MB): about 76 GB without bookkeeping.

Bookkeeping files list every imported module:

- 0.75 MB for 925 imports (810 bytes per import)
- 7.65 MB for 8693 imports (880 bytes per import)
- 7.75 MB for 9143 imports (848 bytes per import)



## Job 2: restore on a fresh runner and build on top

```
runner: 4 cores, 15 GB RAM, 95G free disk
lean: Lean (version 4.33.1, x86_64-unknown-linux-gnu, commit 819816b2e0a3bf405af45ae5c7af2491d8f5bee6, Release)
mathlib: 0df444a360eaa60ab8c11dca51a86af692955474 (clean checkout, prebuilt cache complete)
archive sha256: 9631b4f020199e580ba86178cb56c6e9b09f690c2369a80dc4334aa93f49c7fc
```

| Check | Result | Detail |
|---|---|---|
| Checkpoint restored | INFO | 836 files, 403 MB unpacked |
| Restored slice accepted on a fresh runner without rebuilding | PASS | nothing needed rebuilding |
| On top, first half: files compiled | PASS | 200 of 200, exit code 0, wall 6.8 min, CPU 25.8 min, peak memory of one process 7.5 GB |
| On top, first half: already-built files compiled again | PASS | 0 of 836 |
| On top, second half, bookkeeping deleted during the build: files compiled | PASS | 200 of 200, exit code 0, wall 5.8 min, CPU 22.0 min, peak memory of one process 7.6 GB |
| On top, second half, bookkeeping deleted during the build: already-built files compiled again | PASS | 0 of 1036 |
| Everything still counts as built with all bookkeeping deleted | PASS | nothing needed rebuilding |

Build output by file type:

| File type | Files | Total MB | Average KB |
|---|---|---|---|
| compiled (.olean) | 1236 | 593.3 | 480.1 |
| bookkeeping (.setup.json) | 42 | 321.6 | 7656.6 |
| index (.ilean) | 1236 | 32.4 | 26.2 |
| C output | 1236 | 9.0 | 7.3 |
| trace | 1236 | 5.9 | 4.7 |
| hashes | 3708 | 0.1 | 0.0 |
| all | 8694 | 962.2 | |

Source for these 1236 files: 8.55 MB. Output without bookkeeping: 640.6 MB (74.9 times the source).
Scaled by source size to the whole archive (1030.5 MB): about 77 GB without bookkeeping.

Bookkeeping files list every imported module:

- 7.65 MB for 8699 imports (880 bytes per import)
- 7.65 MB for 8704 imports (879 bytes per import)
- 7.67 MB for 8792 imports (873 bytes per import)


