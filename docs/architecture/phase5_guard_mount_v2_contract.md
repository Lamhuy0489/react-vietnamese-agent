# Guard bootstrap v2: bounded Kaggle PAX adaptation

This is a pre-inference infrastructure deviation, not a research-scope or guard
change. Preserve Dataset v1, bundle03, source commit 7649d5b and all prior receipts.
No GPU was submitted with the rejected mount; no semantic retry is involved.

Kaggle materializes Git's global PAX comment as a regular `pax_global_header`.
V2 accepts this file only at the expanded source root, only for `source.tar.gz`,
and only if its bytes hash to `52 comment=<40-hex frozen source commit>\n`.
Links, wrong contents/commit, nested copies, model sidecars and any other extra
files/directories remain rejected. Verify the full expanded inventory first;
copy executable inputs without this metadata and reverify the original exact
source inventory. Archive mode continues to verify archive and member hashes.

The Dataset manifest, runtime, model snapshot, prompt, generation, task list,
wheels and four-call protocol are unchanged. A separate committed bootstrap
template and generated wrapper get hashes in a new preflight receipt. The kernel
also emits `guard_bootstrap_identity.json` identifying the bootstrap commit and
unchanged Dataset manifest; this is separate from the frozen runtime identity.

The adaptation packager reuses the original Dataset, checks its selected receipt,
both archives and the downloaded header evidence, and creates a fresh kernel-only
output. It runs the full isolated offline archive and expanded-with-real-header
preflights: eight tools/fault recovery, 21 Dummy/completed/missing-only resume,
four-call stub, and source/seal integrity. No new model download/Dataset upload.
Commit/push bootstrap source and receipt, recheck remote READY/private/version
and quota before the first private T4 kernel submission. Audit remote wrapper
bytes and bootstrap identity separately from the completed-probe auditor.
