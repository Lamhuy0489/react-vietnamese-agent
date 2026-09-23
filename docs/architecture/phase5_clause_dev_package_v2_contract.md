# Dev32 source correction v2

The v1 Kaggle run ended ERROR before its first worker started because native
dispatch supplied `constrained` twice. The downloaded source, log and exact
12-file output were authenticated by `audit_phase5_clause_dev_failure_v1.py`.
There were no completed tasks or model-generation receipts. Preserve v1 output.

V2 changes only native forwarding: the admitted guard factory supplies the
constraint evidence root. The explicit synthetic route still supplies its own
root. All frozen task selection, A2/A6 configuration, model identities, decoding,
recovery, guard rules, mock tools and data remain pinned. A new source commit,
package, notebook handle and Kaggle version are required; v1 checkpoints cannot
be resumed under v2.

Before v2 submission, verify native route composition without loading weights,
the full public Dev32 stub in both isolated mount layouts, exact committed
source and remote notebook identity. Run the original fixed 32 tasks only once
under v2. Preserve any semantic failures. Terminal output requires a separate
download and release audit before quality analysis. Held-out Test is untouched.
