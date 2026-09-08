# Guard cancellation / VRAM recovery v1

Three fixed sequential workers on device1; two T4 allocated; no model generation.

| Trial | ACK s (includes load) | Timeout s | Cleanup | Resident GiB | Last residual MiB |
| --- | ---: | ---: | --- | ---: | ---: |
| resident_close | 43.995 | — | TERMINATE/-15 | 3.047 | 0.000 |
| busy_timeout | 30.628 | 120.335 | TERMINATE/-15 | 3.047 | 0.000 |
| ignore_term_timeout | 30.177 | 120.822 | KILL/-9 | 3.047 | 0.000 |

Resource recovery passed all predeclared gates; normal graceful close: False.

Six post-close samples per trial; last three within ±256 MiB of baseline. Full signed residuals, load metrics and lifecycle events are in the receipt.

No sample timestamps, quality inference, agent coexistence or Test. Signed residual = before free minus after free; tolerance is not exact zero leak.

The earlier SAFE-on-B classification miss remains unresolved. This does not establish combined agent/guard fit or accept Phase 5.
