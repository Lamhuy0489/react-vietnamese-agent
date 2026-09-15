# Guard language native-library CPU diagnostic v1

2026-09-16. Follow-up to the finite-language CPU contract; no benchmark inference.
Scope: authenticated Qwen guard tokenizer and Transformers5.5 CPU logits masking.
No model instantiation, weights loading, model.generate, GPU or Test/private GT.

The existing private Dataset manifest is pinned by SHA256. Read only six
tokenizer/config files from its guard archive or expanded layout, match size/hash
against the snapshot and copy to a fresh six-file directory. We deliberately do
not authenticate/read the 3GB weight payload here; this is tokenizer admission,
not permission to load a model. No remote code, download or extra local file is
allowed in AutoTokenizer's materialized input.

Native mode requires Torch2.10.0+cu128, Transformers5.5.0 and tokenizers0.22.2,
and installed logits_process.py must match the manifest-pinned Transformers wheel.
Compile all3069schema combinations with the real tokenizer; no response can be
pruned to meet128tokens including EOS. All combinations round-trip and terminate.

Native masking schedule: indices0,1,2,3,27,111,1022,1023,2045,2046,3066,3068,
every prefix of each path and its terminal. Compare all finite token positions
against the trie; prefer a forbidden token, verify it cannot win and input
scores are unchanged. Preserve a deliberate later ForcedBOS override as negative
evidence, not a native guard fix. Wrong-prompt/empty-allowed/interruption faults
must propagate and leave the original callback usable; restore thread settings.
No monkeypatch of model or Transformers methods is installed by this probe.

Metadata-only mode explicitly reports library_verified=false. Exact local source
archive/expanded mount preflight executes the actual launcher CLI in this mode,
both tokenizer layouts, all8tools,21Dummy and missing-only resume, plus the prior
synthetic token-language probe. Native compatibility remains unverified until
the separate private CPU notebook finishes and version/source/results are audited.

Requested notebook: huylmhuhu/react-vn-guard-language-cpu-v1. CPU/no accelerator,
private/offline, existing guard15 Datasetv1, no external model mount, timeout3600s.
Commit and push source/preflight before submission; preserve every failure and
actual handle/version. No new bare-json-v2 submission or semantic retry.

Successful compatibility does not validate constrained model generation, quality,
utility, A2–A6 stability or Phase5 acceptance. Native guard adapter and strict
processor-composition admission remain separate next steps. Keep timeout fixed.
