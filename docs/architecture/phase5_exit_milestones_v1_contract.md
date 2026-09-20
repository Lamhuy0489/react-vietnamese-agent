# Opt-in process-exit milestones v1

2026-09-20. Diagnostic only; does not replace worker_shutdown_v2 or prove a fix.
No Test/private GT, model weights, network or GPU in the CPU acceptance scope.

## Interface and observation boundary

`MilestoneBackend(factory, MilestoneConfig)` inherits the frozen generate and
cleanup methods. A private spawn-context adapter substitutes only the process
target, wrapping `_observed_serve` with child-local observation. Factory, target
arguments, transport, response, signals and timeout budgets remain unchanged.
The config uses a distinct lifecycle identity; no silent runtime adoption.

The child wraps CPython's `multiprocessing.util._exit_function` and
`threading._shutdown`, delegates exactly once with original arguments and return
value, and restores each hook on return or exception. Host globals are untouched.
This is invasive diagnostic instrumentation, not zero-overhead observation.
Hash the interpreter bootstrap, exit-function and thread-shutdown sources;
admit only an inspected bootstrap with exactly one self.run → util._exit_function
→ threading._shutdown call in source order. This structural check is not a proof
of every future Python version's semantics; exact native rehearsal is required.

Record entered/returned/raised milestones for target, finalizers, threads. Each
fixed slot contains PID, monotonic time and Python-visible live non-daemon thread
count excluding main. No thread names, stacks, exception messages, payloads,
hidden reasoning, CUDA introspection or additional model references. Write the
timestamp last as a publication marker; read only after the worker is reaped.
An absent marker means unobserved, not success. A kill during publication may
lose the last marker; partial prefixes must survive and remain explicitly partial.

Finalizers-returned means the multiprocessing exit function returned, not that
every callback succeeded (stdlib can catch callback exceptions). Thread count
does not enumerate all native/CUDA threads; threads-returned is not process exit
or VRAM recovery. Bind actual reaped PID/exit outcome separately. Observation
cannot change the production two-second graceful budget or manufacture exit0.

## CPU acceptance and next gate

Use the existing six synthetic teardown factories without modifying their source.
Fixed order: fast, bounded, finalizer_block, finalizer_ignore_term,
destructor_block, thread_block; three repeats, two public responses each.
Compare frozen uninstrumented controls and newly observed controls for response,
attempt and exit classifications; timing is descriptive, not equivalence proof.
Fast/bounded finish all stages; blocked finalizer enters but does not return;
blocked destructor cannot return target; blocked thread finishes finalizers but
does not return thread shutdown. All workers must be reaped. Preserve failures,
no semantic retries. Checkpoint each case to fresh output; identity pins exact
working tree plus Git base (not a committed native release).

Tests must cover delegation/exception propagation and restoration, marker schema,
PID/order binding, absent/partial markers, live-snapshot rejection, distinct config,
unchanged inherited methods, host isolation and six real spawn controls. Audit
twice from saved records with hashes. Frozen source hashes remain unchanged.
Only after this CPU gate: wire a separate native runner/receipt join and package,
rehearse the exact native interpreter, freeze source, then submit a separately
identified bounded Kaggle diagnostic. Do not resubmit constrained GPU v1.
