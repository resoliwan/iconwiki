# Material-first loading and worker search — 2026-10-09

Measurements taken locally before deployment.

## Method

Baseline: `158100962b291034e9531e863bb06500e3ec2352`.
Compared the baseline with the working tree using the Codex in-app browser on the
same Mac. Three alternating cold runs per version; 10 searches per run after all
48 libraries loaded. AI expansion disabled. No CPU throttling.

The local measurement server gzip-compresses responses, disables HTTP caching,
adds a 40 ms delay per response, and shares a 10 Mbps byte budget across requests.
This approximates a constrained connection; it is not a production CDN measurement
or an exact network emulator. External Google Fonts responses are outside this
local byte budget. The Material icon font is local and inside the budget.

First display is measured by detecting result cards, waiting for the Material
font when used, then allowing two animation frames. It is a render-ready proxy,
not a pixel-level paint trace. Search latency ends at the next animation frame
after the grid update. Input-handler duration measures synchronous main-thread
work caused by the input event, not total end-to-end interaction latency.

## Final repeat on the saved benchmark scripts

| Metric (median) | Before | After |
|---|---:|---:|
| First icons ready to display | 4,324.5 ms | 963.1 ms |
| All libraries ready | 4,324.5 ms | 4,347.5 ms |
| Synchronous input handling (30 searches) | 56.7 ms | 0.3 ms |
| Input to results frame (30 searches) | 59.1 ms | 54.8 ms |
| Main-thread tasks lasting at least 50 ms, per run | 8, 8, 9 | 0, 0, 0 |

First-display samples (ms): before `[4365.3, 4324.5, 4315.6]`,
after `[963.1, 960.2, 964.2]`.
All-ready samples (ms): before `[4365.3, 4324.5, 4315.6]`,
after `[4352.9, 4347.5, 4338.1]`.

First display was about **78% earlier**. This does not reduce the total catalog
payload (about 52.7 MB before compression), and overall download completion time
is effectively unchanged. The principal search improvement is removing blocking
work from the UI; the search algorithm remains a full scan. The modest result
latency difference should not be treated as a guaranteed speedup.

Queries: `cat`, `arrow`, `arrow down`, `home`, `face`, `a`, `search`, `heart`,
`zznonexistent`, and empty browse. Counts matched in both versions:
462, 5657, 1455, 905, 2605, 218, 738, 1177, 0, 117965.

## Correctness checks

29 Node tests pass, including the actual worker protocol and full catalog data.
Verified that no other catalog is requested before the Material first-display
acknowledgement; remaining concurrency is bounded; primary failure permits the
other libraries to load; failed libraries can be retried independently. Worker
checks cover Material-only search, full-search counts, pagination, library filters,
and resolution of a detail link outside the visible result batch.

Browser checks covered search results, load-more, and successive query changes.

## Reproduce

Run `python3 scripts/benchmark_server.py`, then open
`http://127.0.0.1:4175/benchmark`. The page runs all six comparisons and displays
individual timings and long tasks as JSON. `--baseline` and `--port` are optional.
This server is exclusively a development measurement utility. Production remains
a static site with a browser Web Worker and no search backend.


## Input scheduling added before deployment

The table above measures the worker/progressive-loading change before the later
80 ms input debounce. The deployed automatic search intentionally adds up to
80 ms of idle waiting; Enter bypasses that delay. The saved benchmark script will
include this delay when rerun against the final code. Three additional tests cover
burst coalescing, immediate Enter without a duplicate search, and IME composition.
