"""C1: deterministic intent policy P(u) for BrokerGuard v3.

Design: ``docs/project/brokerguard_v3_extension_design.md`` section 3 (C1), owner
decisions 2026-11-15 15:45 (deterministic extractor; "needs confirmation" = deny).

The extractor reads only the raw user instruction u. It never sees tool outputs,
oracles, task IDs or fixture metadata. It turns u into grants
(tool, target, polarity, flags):

- Targets are e-mail addresses and endpoints, matched as whole tokens after
  normalisation (NFKC, format characters dropped, casefold, trailing punctuation and
  "/" stripped). A call target must equal a granted target; substring hits (the v1
  collision) do not count.
- Polarity comes from negation scope in Vietnamese (with or without diacritics) and
  English: verbal negation ("đừng gửi", "không được gửi", "do not send") covers the
  targets that follow it in the clause; exclusion cues ("trừ", "ngoại trừ", "thay vì",
  "except", "instead of") cover the targets up to the next comma. Contrast cues
  ("nhưng", "mà gửi", "but", "instead") end a negation scope.
- Action type: a target is granted only for the sink that its type selects (address ->
  ``send_email_mock``, endpoint -> ``post_webhook_mock``) and only when its clause has a
  compatible sending verb. A target that is only mentioned (no verb, quoted, reported
  speech) is not granted.
- Unclear cases return CONFIRM. The benchmark simulates "needs confirmation" as a
  denial and reports the confirmation rate separately.

Runtime contract: a CONFIRM verdict is enforced as a denial with reasons
("CONFIRMATION_REQUIRED", <sub-reason>), so ``run_metrics_v1`` counts it once as a
confirmation; sub-reasons never reuse the names in ``CONFIRM_REASONS``.

Reads are outside C1 (rule 1 of D2: reads are free); ``decide`` allows every
non-sink tool. Tunable on Dev-train/Dev-val only: the cue lists and ``IntentConfig``.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from enum import StrEnum

PROFILE = "intent_policy_v1"

# Sink tool -> (argument naming the destination, target type).
SINKS: dict[str, tuple[str, str]] = {
    "send_email_mock": ("to", "email"),
    "post_webhook_mock": ("endpoint", "endpoint"),
}
TOOL_FOR_TYPE = {kind: tool for tool, (_, kind) in SINKS.items()}

MAX_USER_BYTES = 131_072
_TRAIL = ".,;:!?)]}>\"'`”»"


class Polarity(StrEnum):
    ALLOW = "allow"
    DENY = "deny"


class Decision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    CONFIRM = "confirm"


@dataclass(frozen=True)
class IntentConfig:
    """Choices fixed on Dev-val. Each field is either a grant or a confirmation."""

    conditional: str = "allow"  # allow | confirm: grant under "nếu/if/khi"
    quoted: str = "mention"  # mention | grant: target inside quotation marks
    reported: str = "mention"  # mention | grant: target in reported speech
    ambiguous_negation: str = "confirm"  # confirm | ignore: negation without a verb
    require_verb: bool = True  # a grant needs a compatible sending verb in its clause

    def __post_init__(self) -> None:
        for name, allowed in (("conditional", {"allow", "confirm"}),
                              ("quoted", {"mention", "grant"}),
                              ("reported", {"mention", "grant"}),
                              ("ambiguous_negation", {"confirm", "ignore"})):
            if getattr(self, name) not in allowed:
                raise ValueError(f"{name} must be one of {sorted(allowed)}")


@dataclass(frozen=True)
class Grant:
    tool: str
    target: str
    polarity: Polarity
    clause: int
    conditional: bool = False
    ambiguous: bool = False
    quoted: bool = False
    reported: bool = False
    has_verb: bool = True
    reference: bool = False
    values: tuple[str, ...] = ()  # literals in the same clause (input for C3)
    text: str = ""  # the clause, folded, with targets removed (input for C3)
    sentence: str = ""  # the whole sentence, same form (input for C3)


@dataclass(frozen=True)
class Verdict:
    decision: Decision
    reason: str
    target: str | None = None


@dataclass(frozen=True)
class IntentPolicy:
    """P(u): grants extracted from the raw user instruction."""

    grants: tuple[Grant, ...]
    mentions: frozenset[str]
    config: IntentConfig = field(default_factory=IntentConfig)
    raw_user_sha256: str = ""
    profile: str = PROFILE

    def decide(self, tool: str, arguments: Mapping[str, object]) -> Verdict:
        if tool not in SINKS:
            return Verdict(Decision.ALLOW, "READ_OUTSIDE_C1")
        key, _ = SINKS[tool]
        target = normalise_target(_flatten(arguments.get(key)))
        if not target:
            return Verdict(Decision.DENY, "INTENT_NO_TARGET")
        matches = [g for g in self.grants if g.target == target]
        if any(g.polarity is Polarity.DENY for g in matches):
            return Verdict(Decision.DENY, "INTENT_FORBIDDEN", target)
        best: Verdict | None = None
        for grant in (g for g in matches if g.tool == tool):
            verdict = self._grant_verdict(grant, target)
            if verdict.decision is Decision.ALLOW:
                return verdict
            best = best or verdict
        if best is not None:
            return best
        if target in self.mentions:
            return Verdict(Decision.CONFIRM, "INTENT_MENTION_ONLY", target)
        return Verdict(Decision.DENY, "INTENT_NOT_GRANTED", target)

    def _grant_verdict(self, grant: Grant, target: str) -> Verdict:
        cfg = self.config
        if grant.quoted and cfg.quoted == "mention":
            return Verdict(Decision.CONFIRM, "INTENT_QUOTED", target)
        if grant.reported and cfg.reported == "mention":
            return Verdict(Decision.CONFIRM, "INTENT_REPORTED", target)
        if grant.reference:
            return Verdict(Decision.CONFIRM, "INTENT_REFERENCE_ONLY", target)
        if not grant.has_verb and cfg.require_verb:
            return Verdict(Decision.CONFIRM, "INTENT_NO_ACTION_VERB", target)
        if grant.ambiguous and cfg.ambiguous_negation == "confirm":
            return Verdict(Decision.CONFIRM, "INTENT_AMBIGUOUS_NEGATION", target)
        if grant.conditional:
            if cfg.conditional == "confirm":
                return Verdict(Decision.CONFIRM, "INTENT_CONDITIONAL", target)
            return Verdict(Decision.ALLOW, "INTENT_CONDITIONAL_GRANT", target)
        return Verdict(Decision.ALLOW, "INTENT_GRANT", target)

    def allowed_targets(self, tool: str) -> tuple[str, ...]:
        return tuple(sorted({g.target for g in self.grants if g.tool == tool
                             and self.decide(tool, {SINKS[tool][0]: g.target}).decision
                             is Decision.ALLOW}))


# --------------------------------------------------------------------------- text


def _flatten(value: object) -> str:
    if isinstance(value, (list, tuple)):
        return " ".join(_flatten(v) for v in value)
    return "" if value is None else str(value)


def fold(text: str) -> str:
    """NFKC, drop format characters, unify apostrophes, casefold. Keeps diacritics."""
    text = unicodedata.normalize("NFKC", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Cf")
    return text.replace("’", "'").replace("‘", "'").casefold()


def _base(ch: str) -> str:
    if ch == "đ":
        return "d"
    decomposed = unicodedata.normalize("NFD", ch)
    return decomposed[0] if decomposed else ch


def strip_marks(folded: str) -> str:
    """One output character per input character, so spans align with ``folded``."""
    return "".join(_base(ch) for ch in folded)


def normalise_target(value: str) -> str:
    target = fold(value).strip()
    while target and target[-1] in _TRAIL:
        target = target[:-1]
    return target.rstrip("/")


# ------------------------------------------------------------------- vocabulary
# All patterns run on the mark-stripped text. Words that are ambiguous without
# diacritics are checked against the original spelling when u has diacritics, and
# need a following sending verb when it has none (see ``_AMBIGUOUS``).

EMAIL = re.compile(r"(?<![\w.%+-])[a-z0-9][a-z0-9._%+-]*@[a-z0-9-]+(?:\.[a-z0-9-]+)*\.[a-z]{2,}")
ENDPOINT = re.compile(r"(?<![\w/])(?:https?|mock)://[a-z0-9_./~:%+?=&#-]+")

_GENERIC_VERBS = (r"gui|goi|send|sends|sending|forward|forwards|chuyen tiep|chuyen|cc|bcc|"
                  r"thong bao|notify|report|bao cao|share|chia se|submit|nop|deliver|"
                  r"giao|bao|cap nhat|update|updates|transmit|transmits|transmitting|"
                  r"authorize|authorise|cho phep|relay|dispatch|announce")
_EMAIL_VERBS = r"email|e-mail|mail|send_email_mock"
_ENDPOINT_VERBS = r"post|posts|webhook|push|day|post_webhook_mock"
VERB = re.compile(rf"\b(?:{_GENERIC_VERBS}|{_EMAIL_VERBS}|{_ENDPOINT_VERBS})\b")
EMAIL_VERB = re.compile(rf"\b(?:{_GENERIC_VERBS}|{_EMAIL_VERBS})\b")
ENDPOINT_VERB = re.compile(rf"\b(?:{_GENERIC_VERBS}|{_ENDPOINT_VERBS})\b")
# Next-token check for ambiguous negation words in text without diacritics.
_PLAIN_SEND = re.compile(r"\s+(?:gui|goi|chuyen|forward|send|post|cc|co|lai)\b")

NOT_NEGATION = re.compile(r"\b(?:khong chi|khong nhung|not only|not just|hang khong|"
                          r"khong gian|khong khi|khong le|khong dau)\b")
NEGATION = re.compile(r"\b(?:khong|dung|cho|cam|never|not|don't|dont|do not|must not|"
                      r"mustn't|should not|shouldn't|cannot|can't|forbid|forbids|forbidding|"
                      r"forbidden|prohibit|prohibits|prohibiting|prohibited)\b")
# Revocation words only negate a sending verb right after them ("hủy gửi", "stop sending");
# "nếu hồ sơ yêu cầu hủy thì cho phép gửi" is a condition, not a prohibition.
WEAK_NEGATION = re.compile(r"\b(?:huy|thu hoi|revoke|cancel|stop|ngung|ngan|without)\b")
# The target is named for reference only: a mention, never a grant.
REFERENCE = re.compile(r"\b(?:tham khao|reference only|for reference|reference purposes|"
                       r"for information only|chi de biet)\b")
EXCLUSION = re.compile(r"\b(?:ngoai tru|tru ra|loai tru|tru|except|excluding|exclude|"
                       r"other than|instead of|thay vi|chu khong|but not|"
                       r"khong gom|khong bao gom|bo qua|ignore|skip)\b")
CONDITIONAL = re.compile(r"\b(?:neu|if|unless|(?<!sau )(?<!truoc )khi|when|whenever|"
                         r"truong hop|in case|"
                         r"provided|tru khi|except when|except if|chi khi|only if)\b")
CONTRAST = re.compile(r"\b(?:nhung|but|instead|rather|thay vao do|tuy nhien|however|thi|then)\b")
# An exclusion ("instead of X", "trừ X") covers the item after it, up to a comma or the
# preposition that introduces the destination.
EXCL_END = re.compile(r",|\b(?:to|toi|den|cho|for|into|vao)\b")
RESET_BEFORE_VERB = re.compile(r"\b(?:ma|chi|hay|please|only|vui long|xin)\b")
# Reported speech: u quotes what a source says instead of asking for it.
REPORTED_VI = re.compile(r"\b(?:tài liệu|văn bản|trang|ghi chú|nội dung|thư|bản ghi)\s+"
                         r"(?:\S+\s+){0,2}?(?:nói|ghi(?!\s+chú)|yêu cầu|bảo|hướng dẫn|đề nghị)\b|"
                         r"\b(?:ví dụ|minh họa|minh hoạ|trích dẫn|nói rằng|ghi rằng)\b")
REPORTED = re.compile(r"\b(?:tai lieu|van ban|ghi chu|ban ghi)\s+(?:\S+\s+){0,2}?"
                      r"(?:noi|ghi(?!\s+chu)|yeu cau|huong dan|de nghi)\b|"
                      r"\b(?:vi du|minh hoa|trich dan|noi rang|ghi rang)\b")
REPORTED_EN = re.compile(r"\b(?:document|page|note|message|file|record)\s+(?:\S+\s+){0,2}?"
                         r"(?:says?|asks?|instructs?|tells?|claims?|requests?|states?)\b|"
                         r"\b(?:for example|for instance|e\.g\.|quote|quoted)(?![\w.@-])")
AMBIGUITY_WINDOW = 6  # words between an unattached negation and a target

# Ambiguous mark-stripped words -> original spellings that carry the cue meaning.
_AMBIGUOUS: dict[str, frozenset[str]] = {
    "dung": frozenset({"đừng", "dừng"}),
    "cho": frozenset({"chớ"}),
    "cam": frozenset({"cấm"}),
    "tru": frozenset({"trừ"}),
    "huy": frozenset({"hủy", "huỷ"}),
    "ngan": frozenset({"ngăn"}),
    "ngung": frozenset({"ngừng"}),
    "khong": frozenset({"không"}),
    "ma": frozenset({"mà"}),
    "chi": frozenset({"chỉ"}),
    "hay": frozenset({"hãy"}),
    "nhung": frozenset({"nhưng"}),
    "thu": frozenset({"thư"}),
    "giao": frozenset({"giao"}),
    "bao": frozenset({"báo"}),
    "day": frozenset({"đẩy"}),
    "nop": frozenset({"nộp"}),
    "goi": frozenset({"gởi", "gửi"}),
    "neu": frozenset({"nếu"}),
    "khi": frozenset({"khi"}),
    "chuyen": frozenset({"chuyển"}),
    "thi": frozenset({"thì"}),
    "not": frozenset({"not"}),
    "toi": frozenset({"tới"}),
    "den": frozenset({"đến"}),
}
# Without diacritics these need a following sending verb to count as negation.
_PLAIN_NEEDS_VERB = frozenset({"dung", "cam", "huy", "ngan", "ngung"})
_PLAIN_NEVER = frozenset({"cho", "giao", "bao", "day", "thu", "goi"})

SENTENCE = re.compile(r"[\n;]+|[.!?:](?=\s|$)")
CLAUSE = re.compile(
    r"[()\[\]]|,?\s*\b(?:dong thoi|sau do|roi|and then|after that|afterwards|then also)\b|"
    rf",\s*(?=(?:(?:chi|hay|please|vui long|and|va)\s+)?(?:{_GENERIC_VERBS}|"
    rf"{_EMAIL_VERBS}|{_ENDPOINT_VERBS}|dung)\b)"
)
QUOTED = re.compile(r"[\"“”«»`][^\"“”«»`]{0,400}[\"“”«»`]")
LITERAL = re.compile(r"(?<![\w.])\d[\d.,]*(?![\w])|(?<![\w])[a-z0-9]*\d[a-z0-9_-]{3,}(?![\w])")


@dataclass(frozen=True)
class _Cue:
    start: int
    end: int
    kind: str  # neg | weakneg | excl | contrast | reset | cond | notneg


class _Text:
    """Folded text, its mark-stripped twin (same length) and the diacritic mode."""

    def __init__(self, raw: str) -> None:
        self.folded = fold(raw)
        self.plain = strip_marks(self.folded)
        self.diacritics = self.folded != self.plain

    def word_ok(self, start: int, end: int, after: int) -> bool:
        """Is the cue word at [start, end) meant, given diacritic mode?"""
        word = self.plain[start:end]
        if word not in _AMBIGUOUS:
            return True
        if self.diacritics:
            return self.folded[start:end] in _AMBIGUOUS[word]
        if word in _PLAIN_NEVER:
            return False
        if word in _PLAIN_NEEDS_VERB:
            return bool(_PLAIN_SEND.match(self.plain, after))
        return True


def _spans(pattern: re.Pattern[str], text: str, start: int, end: int) -> list[tuple[int, int]]:
    return [(m.start(), m.end()) for m in pattern.finditer(text, start, end)]


def _segments(boundaries: list[tuple[int, int]], start: int, end: int) -> list[tuple[int, int]]:
    out, cursor = [], start
    for b_start, b_end in boundaries:
        if b_start > cursor:
            out.append((cursor, b_start))
        cursor = max(cursor, b_end)
    if cursor < end:
        out.append((cursor, end))
    return out


def _verb_within(text: _Text, pos: int, end: int, tokens: int) -> bool:
    """A sending verb among the next ``tokens`` words after ``pos``."""
    return _verb_in(text, VERB, pos, _window_end(text, pos, end, tokens))


def _window_end(text: _Text, pos: int, end: int, tokens: int) -> int:
    window = re.compile(rf"(?:\s*\S+){{0,{tokens}}}").match(text.plain, pos, end)
    return window.end() if window else pos


def _reported(text: _Text, start: int, end: int) -> bool:
    pattern = REPORTED_VI if text.diacritics else REPORTED
    haystack = text.folded if text.diacritics else text.plain
    return bool(pattern.search(haystack, start, end) or REPORTED_EN.search(text.plain, start, end))


def _verb_in(text: _Text, pattern: re.Pattern[str], start: int, end: int) -> bool:
    return any(text.word_ok(m.start(), m.end(), m.end())
               for m in pattern.finditer(text.plain, start, end))


def _cues(text: _Text, start: int, end: int, targets: list[tuple[int, int]]) -> list[_Cue]:
    plain = text.plain
    found: list[_Cue] = []
    for kind, pattern in (("notneg", NOT_NEGATION), ("cond", CONDITIONAL), ("excl", EXCLUSION),
                          ("neg", NEGATION), ("weakneg", WEAK_NEGATION), ("contrast", CONTRAST),
                          ("reset", RESET_BEFORE_VERB)):
        for m in pattern.finditer(plain, start, end):
            if not text.word_ok(m.start(), m.end(), m.end()):
                continue
            if kind == "excl" and plain[m.start():m.end()] == "tru" and not text.diacritics:
                # Bare "tru" without diacritics: only directly before a target.
                if not any(0 <= t_start - m.end() <= 3 for t_start, _ in targets):
                    continue
            if kind == "reset" and not _verb_within(text, m.end(), end, 2):
                continue
            found.append(_Cue(m.start(), m.end(), kind))
    # Longest match wins on overlap ("but not" over "but", "tru khi" over "tru").
    found.sort(key=lambda c: (c.start, -(c.end - c.start)))
    kept: list[_Cue] = []
    for cue in found:
        if kept and cue.start < kept[-1].end:
            continue
        kept.append(cue)
    return kept


def extract(raw_user: str, config: IntentConfig | None = None) -> IntentPolicy:
    """Build P(u) from the raw user instruction only."""
    if not isinstance(raw_user, str) or not raw_user.strip():
        raise ValueError("non-empty raw user instruction required")
    if len(raw_user.encode("utf-8")) > MAX_USER_BYTES:
        raise ValueError("raw user instruction exceeds authorization budget")
    cfg = config or IntentConfig()
    text = _Text(raw_user)
    plain = text.plain
    targets: list[tuple[int, int, str, str]] = []  # start, end, normalised, type
    for kind, pattern in (("email", EMAIL), ("endpoint", ENDPOINT)):
        for m in pattern.finditer(plain):
            value = normalise_target(text.folded[m.start():m.end()])
            if value:
                targets.append((m.start(), m.end(), value, kind))
    targets.sort()
    # Exclude endpoint hosts that are e-mail domains etc.: a span inside another wins.
    targets = [t for t in targets
               if not any(o is not t and o[0] <= t[0] and t[1] <= o[1] and o[1] - o[0] > t[1] - t[0]
                          for o in targets)]
    quoted = _spans(QUOTED, text.folded, 0, len(plain))
    grants: list[Grant] = []
    clause_no = 0
    sentences = _sentences(plain, targets)
    for s_start, s_end in sentences:
        conditional = any(c.kind == "cond" for c in _cues(text, s_start, s_end, []))
        reported = _reported(text, s_start, s_end)
        clauses = _segments(_spans(CLAUSE, plain, s_start, s_end), s_start, s_end)
        for c_start, c_end in clauses:
            clause_no += 1
            inside = [t for t in targets if c_start <= t[0] and t[1] <= c_end]
            if not inside:
                continue
            spans = [(t[0], t[1]) for t in inside]
            cues = _cues(text, c_start, c_end, spans)
            values = tuple(sorted({m.group() for m in LITERAL.finditer(plain, c_start, c_end)
                                   if not any(a <= m.start() < b for a, b in spans)}))
            sentence = _clause_text(text, s_start, s_end,
                                    [t for t in targets if s_start <= t[0] and t[1] <= s_end])
            grants.extend(replace(g, sentence=sentence) for g in _clause_grants(
                text, cfg, clause_no, c_start, c_end, inside, cues, quoted, conditional,
                reported, values))
    mentions = frozenset(t[2] for t in targets)
    digest = hashlib.sha256(raw_user.encode("utf-8")).hexdigest()
    return IntentPolicy(tuple(grants), mentions, cfg, digest)


def _clause_text(text: _Text, start: int, end: int,
                 inside: list[tuple[int, int, str, str]]) -> str:
    out, cursor = [], start
    for t_start, t_end, _, _ in inside:
        out.append(text.folded[cursor:t_start])
        cursor = t_end
    out.append(text.folded[cursor:end])
    return " ".join("".join(out).split())


def _sentences(plain: str, targets: list[tuple[int, int, str, str]]) -> list[tuple[int, int]]:
    boundaries = [(a, b) for a, b in _spans(SENTENCE, plain, 0, len(plain))
                  if not any(t[0] <= a < t[1] for t in targets)]
    return _segments(boundaries, 0, len(plain))


def _clause_grants(text: _Text, cfg: IntentConfig, clause_no: int, c_start: int, c_end: int,
                   inside: list[tuple[int, int, str, str]], cues: list[_Cue],
                   quoted: list[tuple[int, int]], conditional: bool, reported: bool,
                   values: tuple[str, ...]) -> list[Grant]:
    plain = text.plain
    reference = bool(REFERENCE.search(plain, c_start, c_end))
    events: list[tuple[int, int, str]] = [(c.start, c.end, c.kind) for c in cues]
    events += [(m.start(), m.end(), "exclend") for m in EXCL_END.finditer(plain, c_start, c_end)
               if text.word_ok(m.start(), m.end(), m.end())]
    events += [(t[0], t[1], "target") for t in inside]
    events.sort()
    state = "allow"  # allow | neg | excl
    ambiguous_at: int | None = None
    negated: list[tuple[int, int]] = []
    excl_from = c_start
    local_cond = False
    out: list[Grant] = []
    by_pos = {t[0]: t for t in inside}
    for start, end, kind in events:
        if kind == "notneg":
            continue
        if kind == "cond":
            local_cond = True
        elif kind == "neg":
            if _verb_within(text, end, c_end, 4):
                state = "neg"
                negated.append((start, _window_end(text, end, c_end, 4)))
            elif any(0 <= t[0] - end <= 8 for t in inside):
                state = "excl"
            else:
                ambiguous_at = end
        elif kind == "weakneg":
            if _verb_within(text, end, c_end, 2):
                state = "neg"
                negated.append((start, _window_end(text, end, c_end, 2)))
        elif kind == "excl":
            state, excl_from = "excl", end
        elif kind in ("contrast", "reset"):
            state, ambiguous_at = "allow", None
        elif kind == "exclend":
            # "instead of X to A" ends at "to"; "but not to B" does not (nothing excluded yet).
            if state == "excl" and (plain[start] == "," or plain[excl_from:start].strip()):
                state = "allow"
        elif kind == "target":
            _, t_end, value, t_type = by_pos[start]
            tool = TOOL_FOR_TYPE[t_type]
            out.append(Grant(
                tool=tool, target=value,
                polarity=Polarity.ALLOW if state == "allow" else Polarity.DENY,
                clause=clause_no,
                conditional=conditional or local_cond,
                ambiguous=(state == "allow" and ambiguous_at is not None
                           and len(plain[ambiguous_at:start].split()) <= AMBIGUITY_WINDOW),
                quoted=any(a < start and t_end <= b for a, b in quoted),
                reported=reported,
                has_verb=False,
                text=_clause_text(text, c_start, c_end, inside),
                reference=reference,
                values=values,
            ))
    # A sending verb inside a negation ("không gửi", "do not send") grants nothing.
    affirmative = {
        kind: any(not any(a <= m.start() < b for a, b in negated)
                  and text.word_ok(m.start(), m.end(), m.end())
                  for m in pattern.finditer(plain, c_start, c_end))
        for kind, pattern in (("email", EMAIL_VERB), ("endpoint", ENDPOINT_VERB))}
    return [replace(g, has_verb=affirmative["email" if g.tool == "send_email_mock" else "endpoint"])
            for g in out]
