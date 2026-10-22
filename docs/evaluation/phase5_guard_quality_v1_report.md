# Guard Dev diagnostic — terminal report 2026-10-02

**80/80 requests completed with valid structured verdicts.** All40Dev families
contribute one matched attack/benign pair, eight pairs per surface variant.
Families belong to8conservative groups, so80rows are not80independent mechanisms.
Selection and flag definition were frozen before inference. No Test/private GT,
agent inference, notebook submission or semantic retry was performed.

| Ground truth | Flagged SUSPICIOUS/MALICIOUS | SAFE | Error/missing |
|---|---:|---:|---:|
| Attack40 | TP21 | FN19 | 0 |
| Benign40 | FP5 | TN35 | 0 |

Attack flag rate21/40=52.5%; benign flag rate5/40=12.5%; correct classification
56/80=70%. Both planned and valid denominators are40per branch because there
were no classification errors. Verdicts:54SAFE,26SUSPICIOUS,0MALICIOUS.
Flags are not runtime blocks or ASR; particularly SUSPICIOUS is not equivalent
to MALICIOUS for every gate. These selected reused Dev data do not establish
held-out/generalization performance, and no threshold was changed after results.

The guard retains the exact closure worker boot/model/tokenizer and prompt hash.
Same ModelGuard interface, temperature0, seed42, max_new_tokens128. Fresh guard
state and task journal per input; evaluation labels are absent from model inputs.

Two GET admission NETWORK_ERROR stops occurred after33completed inputs, before
any POST or started record for input34. Both interruptions remain recorded.
A preregistered additive admission amendment then pinned one authenticated
client for the47never-started inputs, preserving identity/hash validation on
every POST and the150second POST deadline. It changed no model, prompt, decoding,
input or prior result. All80request IDs are unique; every call joins the correct
same-boot started/finished journal with HTTP200. No delivery remains unresolved.
Completed resume creates0new calls. Source snapshot contains636verified files;
repeated saved scoring is identical. Worker availability is a past observation,
not a guarantee of current uptime.

[Protocol](phase5_guard_quality_v1_protocol.md) ·
[Terminal receipt](../../experiments/manifests/phase5_guard_quality_20261002.json) ·
[Closure dossier](phase5_completion_20261002.md).
Raw and manifest:build/evaluation/phase5_guard_quality_native_20261002_01.

The diagnostic confirms the guard is operational but has substantial false
negatives and some benign flags. Phase5 acceptance remains bounded implementation
and smoke validation; these results do not claim the defense is already strong.
Keep the baseline unchanged for this closure. Future guard/policy changes need
new Dev protocols and their own versions; do not rerun this sample for better scores.
