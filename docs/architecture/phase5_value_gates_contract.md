# A6 value PreGate and Post view primitives v1

Bounded next component milestone, not runtime A6 enablement. Preserve every
previous receipt/source/contract. Synthetic-only QA, no benchmark Dev/Test payload.
Read with `phase5_value_origin_contract.md`; old extraction/release profile is unchanged.

## External PreGate

Inputs are the run-local host ArtifactStore/index, raw-user artifact ID, proposed
ActionTurn artifact ID and fixed ToolRegistry. No caller-supplied origin labels,
evaluator grants, guard risk summaries or parsed model-origin declarations.
Proposal must be a derived MODEL_OUTPUT/MODEL artifact containing the exact
ActionTurn, no transformations, and no future observation. Its ancestors must
include the given raw user and **all admitted index roots**. This enforces that
public origin evidence cannot come from an unobserved source. The host remains
responsible for accurate source labels and actual model-context ancestry.
Conversely, every observed raw user/tool-source root in that ancestry must be
admitted: omitting a protected source cannot make an identical public value safe.

Tool input schemas validate strictly before policy. Only the six fixed read/compute
tools are fail-open on missing value origins; unknown tools cannot inherit read
privilege. Invalid host/proposal structure raises; the future runtime must abort
before Broker, not transform integrity failures into ALLOW.

For both email and webhook:

1. Exact action-specific raw-user destination anchors are mandatory. An address
   in a source is not authorization, even if that source is trusted. Destination
   evidence is type-specific EMAIL/URL; no normalization/domain matching.
2. Every critical scalar leaf (to/subject/body or endpoint/payload leaves) must
   have an exact typed origin under the frozen index profile. Strings may match
   any string type; numeric GPA/MONEY requires the matching field name. No
   substring-based payload authorization. Unsupported short strings, booleans,
   nulls, common untyped numbers and empty containers are unknown and deny.
3. Preserve all matching origins; any S1/S2 origin denies even if also public or
   user-authorized. Scan the serialized argument object, including all keys, for
   protected raw/normalized values. A partial public match cannot clear a secret.
4. Webhook structural keys have a fixed small allowlist: message/content/text/
   data/items/student_id/course_code/email/url/endpoint/phone/gpa/amount/money/date/
   internal_record_id/record_id. Unknown keys deny; keys are also scanned for
   protected values. This bounded schema is explicitly restrictive, not tuned.
5. Depth 16, 256 leaves and frozen 128 KiB input limit. Incomplete index, scan
   limit/error, unknown critical field => DENY. No tool execution in this module.

The result stores proposal/user/index hashes, field paths/origin records, protected
matches, reasons and linked artifact IDs. It is **one value gate**, not a full A6
authorization decision: rule/LLM control risks and coarse-session arbitration must
still be composed before a runtime executes it. Current A0–A5 runtime unchanged.

## Post context view

Given a verified untrusted source root and its exact TOOL_RESULT child, create a
new derived artifact containing a versioned JSON data envelope, never raw delimiter
concatenation. Serialized strings escape embedded delimiter/control-like text.
Trusted source returns the existing observation unchanged. Never rewrite raw,
strip detector signals, promote trust or lower sensitivity. Observation content
and result ordering remain recoverable; new view is not admitted as a new origin.
The envelope is a data representation, not proof against semantic prompt injection.
No model sees this view until separately tested runtime integration.

## Remaining

A6 runtime Pre/Post/Final integration, released-final accounting/authorization,
rule/LLM arbitration, efficient guard inference, processing-scope controls and
grouped Dev validation remain open. Tests here may execute the existing Broker
only after an ALLOW value decision with synthetic fixtures, as plumbing evidence;
they are not A6 end-to-end or model quality results.
