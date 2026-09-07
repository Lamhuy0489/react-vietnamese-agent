# Phase 4 foundation v1 — first implementation milestone

Owner authorized Phase 4 on 2026-09-07. Scope: representation and plumbing,
not Phase 5 policy/enforcement. Preserve all measured/frozen source and dataset
bytes; add a separate `react_agent.foundation` package. Existing A0 runtime,
prompts, parser, Broker, evaluator and tool limits are unchanged.

First milestone freezes normalizer/artifact/store APIs. Runtime integration,
ControlState/ContextBundle, pre/post/final hooks and trajectory-level A0 parity
are subsequent Phase 4 work, not implied complete by these primitives.

## Normalizer

`normalize(text, profile)` returns immutable raw and normalized strings,
input/output hashes, Unicode database version, profile version, stage operations
and descriptive features. Named profiles: `raw_v1` identity; `unicode_v1` NFKC;
`security_v1` NFKC, removal of U+200B/U+200C/U+200D/U+2060/U+FEFF, inline
whitespace collapse and CRLF/CR to LF. NEL/Unicode line separator become LF;
Unicode paragraph separator becomes two LF. Preserve existing LF/paragraph breaks.
Reapply NFKC after removal to compose newly adjacent combining characters;
otherwise a second call can differ. No accent restoration, translation,
word-boundary guessing, attack regex or security verdict. Unknown profiles fail.

Raw zero-width positions are recorded before transforms. Stage operations have
stage-local before/after hashes, never falsely claimed to be raw offset maps.
Security normalization may change emoji joiners or compatibility code literals;
this is an explicit optional representation, never silently used by A0 or sent
as tool arguments. Raw remains authoritative. Cache identity includes input
hash, profile/version and Unicode database version. No English-ratio guess is
reported; character statistics have explicit denominators and are not classifiers.

## Artifacts and provenance

`ArtifactStore(run_id)` owns monotonically allocated `ART_<run>_<sequence>` IDs.
Content/metadata are canonical JSON strings in frozen records; decoded objects
are fresh copies so nested mutation cannot change stored content. Stable content
hash covers strict finite JSON with string keys, sorted keys, explicit UTF-8.
Unsupported/nonfinite values fail. Source IDs and runtime IDs remain distinct.
Parent edges carry typed relations. All parents exist in the same store before
the child; future/self edges and duplicate parents fail. No update/delete API.
Import validates identity, sequence, hashes and monotone labels by reconstructing
the store; supplied IDs are verified, never trusted as allocation requests.

Sensitivity `S0 < S1 < S2`; trust uses explicit `TRUSTED`/`UNTRUSTED` per phase4.
Joins are independent and conservative. Root labels are host-owned source
metadata, never assertions extracted from content or evaluator truth. Derivation
cannot reduce sensitivity/increase trust. Normalized views preserve both exactly.
When adapting legacy source labels later, T0 maps to TRUSTED and T1/T2 map
conservatively to UNTRUSTED; preserve the original label as metadata. Do not
infer confidential contents from an attack objective or grant oracle.

Store operations provide parents, children, ancestors, all artifacts and typed
edges; conservative dependency is not causal token-level provenance. Export is
fresh JSONL outside frozen data. No graph database or network service required.

## Verification and remaining gates

Before Dev use, hash-check both seals and confirm the already sealed 50 clean
robustness IDs (IDs only). New validator parses only 150 clean Dev instructions
and 400 adversarial Dev fixtures, never Test payloads or private ground truth.
Check all profiles for determinism/idempotence/raw preservation; run lineage and
label checks. Hash-only Test integrity is allowed, not Test-driven tuning.
This milestone has no model/Broker execution or attack-success metric. Full
phase closure additionally requires pass-through hooks, observable runtime
artifacts, A0 context/action/result parity, smoke/clean/attack Dev trajectories,
performance/memory diagnostics, trace v2 metadata and a reproducible receipt.
