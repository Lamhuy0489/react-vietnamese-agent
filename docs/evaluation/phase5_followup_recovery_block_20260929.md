# Phase 5 follow-up recovery block — 2026-09-29

A new paired worker package/session was prepared and submitted with the frozen
worker source commit `728821ea761b3994eb40ebba91ab8238e4667f82`. Preflight passed
4/4 layouts. The new agent v8 and guard v6 kernels are both `RUNNING`, and
read-only discovery verified both identities as `READY`.

The exact-email follow-up cannot start on the new pair yet. The shared journal
still contains one request from the previous guard session with terminal state
`uncertain`. The runner correctly blocks all new delivery while that record
exists. A new API session does not prove that the old request stopped or was
reconciled. Deleting the record, changing the journal root, or treating kernel
`RUNNING` as request recovery would invalidate the experiment.

## Required recovery boundary

Resolve the old uncertain delivery through a documented worker-level recovery
receipt, or formally close the old experiment as blocked and obtain a separately
authorized experiment epoch whose journal boundary is recorded in the protocol.
The new pair is ready for health/inference once that boundary is valid. Until
then no A4–A6 follow-up requests are sent.

Mainline 14/14 evidence remains immutable and valid. The partial A3 follow-up
receipt remains diagnostic and does not change Phase 5 acceptance.
