#!/usr/bin/env python3
"""
Validate a ticket-test-design Markdown draft (structure + contract coverage).

Catches delivery defects that make the spec unusable:
- missing Summary / Acceptance / Contract readiness / Pack note
- legacy single Readiness line
- must/should/later count mismatch vs case headings
- given AC not covered by must proves (unless Must-deferred)
- must cases without proves; multi-AC proves without (AC-n) tags in then
- should cases without proves or supplements
- must/should missing automate: candidate|manual|n/a
- later sections that look like long scripted steps

Does *not* adjudicate soft should priority, entailment quality, or automate choice correctness.

Exit 0 if OK, 1 if errors.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

__version__ = "1.2.0"

_SUMMARY_RE = re.compile(r"(?m)^##\s*(Summary|摘要)\s*$")
_ACCEPTANCE_RE = re.compile(r"(?m)^##\s*(Acceptance|验收标准)\s*$")
_COUNTS_RE = re.compile(
    r"(?i)(?:\*\*)?(?:Counts|计数)(?:\*\*)?\s*[:：]\s*"
    r"(?:must|必测)\s*(\d+)\s*[·/／]\s*"
    r"(?:should|应测)\s*(\d+)\s*[·/／]\s*"
    r"(?:later|以后)\s*(\d+)"
)
_CONTRACT_READY_RE = re.compile(
    r"(?i)(?:\*\*)?(?:Contract readiness|合同就绪)(?:\*\*)?\s*[:：]\s*(.+)$",
    re.MULTILINE,
)
_PACK_NOTE_RE = re.compile(
    r"(?i)(?:\*\*)?(?:Pack note|应测包)(?:\*\*)?\s*[:：]\s*(.+)$",
    re.MULTILINE,
)
# Exact summary label only — must not match "Contract readiness"
_LEGACY_READINESS_RE = re.compile(
    r"(?im)^\s*[-*]\s*\*\*(?:Readiness|就绪判断)\*\*\s*[:：]",
)
_AUTOMATE_RE = re.compile(
    r"(?m)^\s*automate\s*:\s*(candidate|manual|n/a)\s*$",
    re.IGNORECASE,
)
_TC_HEADER_RE = re.compile(
    r"(?m)^###\s+(TC-\d+)\s*·\s*(must|should)\s*·\s+\S"
)
_LATER_HEADER_RE = re.compile(r"(?m)^##\s*(Later|以后)\s*$")
_AC_GIVEN_RE = re.compile(
    r"(?m)^\s*[-*]\s*\*\*AC-(\d+)\*\*\s*`?\(given\)`?",
)
_MUST_DEFERRED_LINE_RE = re.compile(
    r"(?im)^\s*[-*]\s*\*\*Must-deferred\*\*\s*[:：]\s*(.+)$",
)
_MUST_DEFERRED_AC_RE = re.compile(r"AC-(\d+)")
_PROVES_LINE_RE = re.compile(r"(?m)^\s*proves\s*:\s*(.+)$")
_SUPPLEMENTS_LINE_RE = re.compile(r"(?m)^\s*supplements\s*:\s*\S")
_AC_ID_RE = re.compile(r"AC-(\d+)")
_FULL_COVERAGE_BAN_RE = re.compile(
    r"(?i)\b(full\s+coverage|100%\s*coverage|MECE\s+complete|测试完备)\b"
)
_LATER_SCRIPT_RE = re.compile(
    r"(?ms)^##\s*(?:Later|以后)\s*$.*?(?=^##\s|\Z)"
)
_NUMBERED_STEPS_RE = re.compile(r"(?m)^\s*(\d+\.\s+\S|when:\s|given:\s|then:\s)")
_CONTRACT_READY_OK_RE = re.compile(
    r"(?i)\bcontract-ready\b|合同就绪\s*[（(]?ready|可凭必测\b"
)
# "contract-ready" alone; Chinese may say "合同就绪：contract-ready" or "已就绪"


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Validate ticket-test-design draft (structure + given-AC coverage)."
    )
    p.add_argument("path", nargs="?", help="Markdown file (default: stdin)")
    p.add_argument(
        "--brief",
        action="store_true",
        help="Brief mode: Summary + Acceptance + must cases; should count may be titles-only.",
    )
    p.add_argument("-q", "--quiet", action="store_true")
    return p.parse_args()


def _read_text(path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def _section_after(text: str, header_re: re.Pattern[str]) -> str:
    m = header_re.search(text)
    if not m:
        return ""
    start = m.end()
    nxt = re.search(r"(?m)^##\s+", text[start:])
    end = start + nxt.start() if nxt else len(text)
    return text[start:end]


def _case_blocks(text: str) -> list[tuple[str, str, str]]:
    headers = list(_TC_HEADER_RE.finditer(text))
    out: list[tuple[str, str, str]] = []
    for i, m in enumerate(headers):
        start = m.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        next_h2 = re.search(r"(?m)^##\s+", text[start:end])
        if next_h2:
            end = start + next_h2.start()
        out.append((m.group(1), m.group(2), text[start:end]))
    return out


def _proves_ids(body: str) -> list[str]:
    m = _PROVES_LINE_RE.search(body)
    if not m:
        return []
    return [f"AC-{n}" for n in _AC_ID_RE.findall(m.group(1))]


def _deferred_ids(acceptance: str) -> set[str]:
    out: set[str] = set()
    for m in _MUST_DEFERRED_LINE_RE.finditer(acceptance):
        val = m.group(1).strip()
        if re.match(r"(?i)\(none\)|^none\b|^无\b|^—\s*$|^-\s*$", val):
            continue
        out.update(f"AC-{n}" for n in _MUST_DEFERRED_AC_RE.findall(val))
    return out


def validate(text: str, *, brief: bool = False) -> list[str]:
    errors: list[str] = []

    if not _SUMMARY_RE.search(text):
        errors.append("missing ## Summary (or 摘要)")
    if not _ACCEPTANCE_RE.search(text):
        errors.append("missing ## Acceptance (or 验收标准)")

    if _LEGACY_READINESS_RE.search(text):
        errors.append(
            "legacy Readiness/就绪判断 forbidden — use Contract readiness + Pack note"
        )

    contract_m = _CONTRACT_READY_RE.search(text)
    if not contract_m:
        errors.append("Summary must include Contract readiness / 合同就绪")
    contract_val = contract_m.group(1).strip() if contract_m else ""

    pack_m = _PACK_NOTE_RE.search(text)
    if not pack_m:
        errors.append("Summary must include Pack note / 应测包")

    counts_m = _COUNTS_RE.search(text)
    if not counts_m:
        errors.append(
            "Summary must include Counts/计数: must N · should N · later N"
        )
        must_n = should_n = later_n = None
    else:
        must_n, should_n, later_n = (int(counts_m.group(i)) for i in (1, 2, 3))

    if _FULL_COVERAGE_BAN_RE.search(text):
        errors.append("forbidden claim of full/MECE-complete coverage")

    acceptance = _section_after(text, _ACCEPTANCE_RE)
    given_acs = {f"AC-{n}" for n in _AC_GIVEN_RE.findall(acceptance)}
    deferred = _deferred_ids(acceptance)

    cases = _case_blocks(text)
    must_cases = [c for c in cases if c[1] == "must"]
    should_cases = [c for c in cases if c[1] == "should"]

    if must_n is not None and must_n != len(must_cases):
        errors.append(
            f"must count mismatch: Summary={must_n} headings={len(must_cases)}"
        )
    if not brief and should_n is not None and should_n != len(should_cases):
        errors.append(
            f"should count mismatch: Summary={should_n} headings={len(should_cases)}"
        )

    if must_n == 0 and not re.search(r"(?i)blocked|阻塞", contract_val + text[:800]):
        errors.append(
            "zero must cases requires Contract readiness blocked-* (or 阻塞)"
        )

    if must_n is not None and must_n > 0 and not must_cases:
        errors.append("Summary claims must>0 but no ### TC-… · must · headings")

    proved_by_must: set[str] = set()
    for cid, _prio, body in must_cases:
        ids = _proves_ids(body)
        if not ids:
            errors.append(f"{cid} (must): missing proves: with AC-*")
        proved_by_must.update(ids)
        for key in ("given:", "when:", "then:"):
            if not re.search(rf"(?m)^\s*{re.escape(key)}", body):
                errors.append(f"{cid}: missing {key}")
        if not _AUTOMATE_RE.search(body):
            errors.append(
                f"{cid}: missing automate: candidate|manual|n/a"
            )
        if len(ids) >= 2:
            then_m = re.search(r"(?ms)^\s*then\s*:\s*(.+?)(?=^\s*\w+\s*:|\Z)", body)
            then_blob = then_m.group(1) if then_m else ""
            for ac in ids:
                n = ac.split("-", 1)[1]
                if not re.search(rf"\(AC-{n}\)", then_blob):
                    errors.append(
                        f"{cid}: multi-AC proves requires (AC-{n}) tag in then"
                    )

    # Given-AC coverage invariant
    uncovered = sorted(
        given_acs - proved_by_must - deferred,
        key=lambda x: int(x.split("-")[1]),
    )
    for ac in uncovered:
        errors.append(
            f"given {ac} not proved by any must case "
            f"(add must proves or Must-deferred)"
        )

    unknown_deferred = sorted(deferred - given_acs, key=lambda x: int(x.split("-")[1]))
    for ac in unknown_deferred:
        errors.append(f"Must-deferred {ac} is not a listed (given) AC")

    claims_contract_ready = bool(
        re.search(r"(?i)\bcontract-ready\b", contract_val)
        or re.search(r"合同已就绪|合同可收", contract_val)
    )
    if deferred and claims_contract_ready:
        errors.append(
            "Must-deferred given ACs forbid contract-ready "
            "(use blocked-by-must-deferred)"
        )
    if uncovered and claims_contract_ready:
        errors.append(
            "uncovered given ACs forbid contract-ready"
        )

    if not brief:
        for cid, _prio, body in should_cases:
            for key in ("given:", "when:", "then:"):
                if not re.search(rf"(?m)^\s*{re.escape(key)}", body):
                    errors.append(f"{cid}: missing {key}")
            has_proves = bool(_proves_ids(body))
            has_supp = bool(_SUPPLEMENTS_LINE_RE.search(body))
            if not has_proves and not has_supp:
                errors.append(
                    f"{cid} (should): need proves: (honest) or supplements:"
                )
            if not _AUTOMATE_RE.search(body):
                errors.append(
                    f"{cid}: missing automate: candidate|manual|n/a"
                )

    later_m = _LATER_HEADER_RE.search(text)
    if later_n is not None and later_n > 0 and not later_m:
        errors.append("Summary later>0 but missing ## Later (or 以后)")

    if later_m:
        later_body_m = _LATER_SCRIPT_RE.search(text)
        if later_body_m:
            chunk = later_body_m.group(0)
            if re.search(r"(?m)^\s{4,}(given|when|then)\s*:", chunk):
                errors.append(
                    "Later must be charter/idea only — found given/when/then scripts"
                )
            if len(_NUMBERED_STEPS_RE.findall(chunk)) >= 4:
                errors.append(
                    "Later looks like a numbered script — use charter/idea bullets"
                )

    return errors


def main() -> int:
    args = _parse_args()
    text = _read_text(args.path)
    errors = validate(text, brief=args.brief)
    if errors:
        print(f"FAIL ({len(errors)}) validate_ticket_test_design {__version__}")
        for e in errors:
            print(f"  - {e}")
        return 1
    if not args.quiet:
        print(f"OK validate_ticket_test_design {__version__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
