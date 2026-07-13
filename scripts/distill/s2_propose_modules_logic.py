"""S2 module proposal — Wiki tree + strategy industry seeds (no LLM)."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

SEEDS_PATH = Path(__file__).resolve().parents[2] / "domain-knowledge" / "s2-propose-industry-seeds.json"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
TITLE_PREFIX_RE = re.compile(r"^[\d]{2}[-–—]\s*")
SLUG_SAFE_RE = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class PageRecord:
    page_id: str
    title: str
    space_key: str
    web_ui: str
    theme: str = ""
    facet_dir: str = ""
    body_excerpt: str = ""


@dataclass(frozen=True)
class ModuleSeed:
    slug: str
    name_cn: str
    axis: str
    strategy_dimension_ids: tuple[str, ...]
    keywords: tuple[str, ...]
    facet_hints: tuple[str, ...]
    keyword_res: tuple[re.Pattern[str], ...]


@dataclass
class ProposedModule:
    slug: str
    name_cn: str
    axis: str
    source: str  # industry_seed | wiki_branch | merged
    confidence: str  # high | medium | low
    page_count: int
    page_ids: list[str] = field(default_factory=list)
    sample_titles: list[str] = field(default_factory=list)
    wiki_branch: str = ""
    strategy_dimension_ids: list[str] = field(default_factory=list)
    facet_counts: dict[str, int] = field(default_factory=dict)
    suggested_keywords: list[str] = field(default_factory=list)
    score: int = 0


def load_seeds_config(path: Path | None = None) -> dict[str, Any]:
    cfg_path = path or SEEDS_PATH
    raw = json.loads(cfg_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"invalid seeds config: {cfg_path}")
    return raw


def _compile_keywords(keywords: Sequence[str]) -> tuple[re.Pattern[str], ...]:
    patterns: list[re.Pattern[str]] = []
    for token in keywords:
        t = str(token).strip()
        if not t:
            continue
        if any(ch in t for ch in r".*+?[](){}|^$\\"):
            patterns.append(re.compile(t, re.IGNORECASE))
        else:
            patterns.append(re.compile(re.escape(t), re.IGNORECASE))
    return tuple(patterns)


def parse_module_seeds(cfg: Mapping[str, Any], team: str | None = None) -> list[ModuleSeed]:
    out: list[ModuleSeed] = []
    for row in cfg.get("module_seeds") or []:
        slug = str(row.get("slug") or "").strip()
        if not slug:
            continue
        teams_raw = row.get("teams")
        if isinstance(teams_raw, list) and teams_raw:
            allowed = {str(t).strip().lower() for t in teams_raw if str(t).strip()}
            if team and team.lower() not in allowed:
                continue
            if not team:
                continue
        keywords = tuple(str(x).strip() for x in (row.get("keywords") or []) if str(x).strip())
        out.append(
            ModuleSeed(
                slug=slug,
                name_cn=str(row.get("name_cn") or slug).strip(),
                axis=str(row.get("axis") or "").strip(),
                strategy_dimension_ids=tuple(
                    str(x).strip() for x in (row.get("strategy_dimension_ids") or []) if str(x).strip()
                ),
                keywords=keywords,
                facet_hints=tuple(str(x).strip() for x in (row.get("facet_hints") or []) if str(x).strip()),
                keyword_res=_compile_keywords(keywords),
            )
        )
    return out


def slugify_label(label: str, *, prefix: str = "section") -> str:
    original = label.strip()
    text = TITLE_PREFIX_RE.sub("", original.lower())
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = SLUG_SAFE_RE.sub("-", text).strip("-")
    if not text or text == "untitled":
        digest = hashlib.sha1(original.encode("utf-8")).hexdigest()[:8]
        return f"{prefix}-{digest}"
    if text[0].isdigit():
        text = f"{prefix}-{text}"
    return text[:48].strip("-")


def parse_page_frontmatter(md_path: Path) -> dict[str, str]:
    if not md_path.is_file():
        return {}
    text = md_path.read_text(encoding="utf-8", errors="replace")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        meta[key.strip()] = val.strip().strip('"')
    body = text[match.end() :].strip()
    meta["_body_excerpt"] = body[:800]
    outline = meta.get("kb_outline", "")
    if outline and "/" in outline:
        meta["_facet_dir"] = outline.split("/", 1)[0]
    return meta


def load_page_records(
    descendants: Sequence[Mapping[str, Any]],
    pages_dir: Path,
) -> list[PageRecord]:
    rows: list[PageRecord] = []
    for item in descendants:
        page_id = str(item.get("id") or "").strip()
        if not page_id:
            continue
        meta = parse_page_frontmatter(pages_dir / f"{page_id}.md")
        rows.append(
            PageRecord(
                page_id=page_id,
                title=str(item.get("title") or meta.get("title") or page_id).strip(),
                space_key=str(item.get("spaceKey") or meta.get("space_key") or "").strip(),
                web_ui=str(item.get("webUi") or meta.get("web_ui") or "").strip(),
                theme=str(meta.get("theme") or "").strip(),
                facet_dir=str(meta.get("_facet_dir") or "").strip(),
                body_excerpt=str(meta.get("_body_excerpt") or "").strip(),
            )
        )
    return rows


def wiki_branch_for_page(
    page_id: str,
    root_id: str,
    parent_by_child: Mapping[str, str | None],
    title_by_id: Mapping[str, str],
) -> str:
    cur = page_id
    seen: set[str] = set()
    while cur and cur not in seen:
        seen.add(cur)
        parent = parent_by_child.get(cur)
        if parent == root_id:
            return title_by_id.get(cur, cur)
        if not parent:
            break
        cur = parent
    return ""


def score_page_for_seed(page: PageRecord, seed: ModuleSeed) -> int:
    hay = f"{page.title}\n{page.theme}\n{page.body_excerpt}"
    score = 0
    for pat in seed.keyword_res:
        if pat.search(hay):
            score += 1
    if page.facet_dir and page.facet_dir in seed.facet_hints:
        score += 2
    return score


def is_engineering_noise(page: PageRecord, noise_patterns: Sequence[re.Pattern[str]]) -> bool:
    hay = f"{page.title}\n{page.theme}\n{page.body_excerpt}".lower()
    return any(p.search(hay) for p in noise_patterns)


def assign_pages_to_seeds(
    pages: Sequence[PageRecord],
    seeds: Sequence[ModuleSeed],
) -> dict[str, list[PageRecord]]:
    by_slug: dict[str, list[PageRecord]] = {s.slug: [] for s in seeds}
    for page in pages:
        best_score = 0
        best_slug = ""
        for seed in seeds:
            sc = score_page_for_seed(page, seed)
            if sc > best_score:
                best_score = sc
                best_slug = seed.slug
        if best_slug and best_score > 0:
            by_slug[best_slug].append(page)
    return by_slug


def propose_wiki_branch_modules(
    pages: Sequence[PageRecord],
    root_id: str,
    parent_by_child: Mapping[str, str | None],
    title_by_id: Mapping[str, str],
    *,
    min_branch_pages: int,
    assigned_ids: set[str],
) -> list[ProposedModule]:
    branch_pages: dict[str, list[PageRecord]] = defaultdict(list)
    for page in pages:
        if page.page_id in assigned_ids:
            continue
        branch = wiki_branch_for_page(page.page_id, root_id, parent_by_child, title_by_id)
        if branch:
            branch_pages[branch].append(page)

    proposals: list[ProposedModule] = []
    for branch, group in sorted(branch_pages.items(), key=lambda kv: -len(kv[1])):
        if len(group) < min_branch_pages:
            continue
        slug = slugify_label(branch)
        proposals.append(
            ProposedModule(
                slug=slug,
                name_cn=branch,
                axis="Wiki 一级分支（待映射 strategy 维度）",
                source="wiki_branch",
                confidence="medium" if len(group) >= min_branch_pages * 2 else "low",
                page_count=len(group),
                page_ids=[p.page_id for p in group],
                sample_titles=[p.title for p in group[:8]],
                wiki_branch=branch,
                suggested_keywords=_top_title_tokens(group),
                score=len(group),
            )
        )
    return proposals


def _top_title_tokens(pages: Sequence[PageRecord], limit: int = 12) -> list[str]:
    tokens: Counter[str] = Counter()
    for page in pages:
        for part in re.split(r"[\s/|—–\-:]+", page.title.lower()):
            part = part.strip()
            if len(part) >= 3 and not part.isdigit():
                tokens[part] += 1
    return [t for t, _ in tokens.most_common(limit)]


def build_seed_proposals(
    pages: Sequence[PageRecord],
    seeds: Sequence[ModuleSeed],
    by_seed_pages: Mapping[str, list[PageRecord]],
    *,
    min_pages: int,
) -> list[ProposedModule]:
    proposals: list[ProposedModule] = []
    for seed in seeds:
        group = list(by_seed_pages.get(seed.slug) or [])
        if not group:
            continue
        facet_counts = Counter(p.facet_dir for p in group if p.facet_dir)
        total_score = sum(score_page_for_seed(p, seed) for p in group)
        confidence = "high" if len(group) >= min_pages and total_score >= len(group) else "medium"
        if len(group) < min_pages:
            confidence = "low"
        proposals.append(
            ProposedModule(
                slug=seed.slug,
                name_cn=seed.name_cn,
                axis=seed.axis,
                source="industry_seed",
                confidence=confidence,
                page_count=len(group),
                page_ids=[p.page_id for p in group],
                sample_titles=[p.title for p in group[:8]],
                strategy_dimension_ids=list(seed.strategy_dimension_ids),
                facet_counts=dict(facet_counts),
                suggested_keywords=list(seed.keywords[:16]),
                score=total_score,
            )
        )
    return proposals


def merge_proposals(
    seed_proposals: Sequence[ProposedModule],
    branch_proposals: Sequence[ProposedModule],
) -> list[ProposedModule]:
    by_slug: dict[str, ProposedModule] = {}
    for prop in seed_proposals:
        by_slug[prop.slug] = prop
    for prop in branch_proposals:
        if prop.slug in by_slug:
            existing = by_slug[prop.slug]
            merged_ids = sorted(set(existing.page_ids) | set(prop.page_ids))
            by_slug[prop.slug] = ProposedModule(
                slug=existing.slug,
                name_cn=existing.name_cn,
                axis=existing.axis,
                source="merged",
                confidence=existing.confidence if existing.confidence != "low" else prop.confidence,
                page_count=len(merged_ids),
                page_ids=merged_ids,
                sample_titles=existing.sample_titles or prop.sample_titles,
                wiki_branch=prop.wiki_branch or existing.wiki_branch,
                strategy_dimension_ids=existing.strategy_dimension_ids,
                facet_counts=existing.facet_counts,
                suggested_keywords=sorted(set(existing.suggested_keywords) | set(prop.suggested_keywords)),
                score=existing.score + prop.score,
            )
        else:
            by_slug[prop.slug] = prop
    return sorted(by_slug.values(), key=lambda p: (-p.page_count, p.slug))


def estimate_non_business(
    pages: Sequence[PageRecord],
    assigned_ids: set[str],
    noise_patterns: Sequence[re.Pattern[str]],
) -> dict[str, Any]:
    unassigned = [p for p in pages if p.page_id not in assigned_ids]
    noise = [p for p in unassigned if is_engineering_noise(p, noise_patterns)]
    return {
        "unassigned_page_count": len(unassigned),
        "engineering_noise_count": len(noise),
        "sample_noise_titles": [p.title for p in noise[:12]],
    }


def propose_modules(
    *,
    root_id: str,
    pages: Sequence[PageRecord],
    parent_by_child: Mapping[str, str | None] | None,
    title_by_id: Mapping[str, str] | None,
    seeds_cfg: Mapping[str, Any] | None = None,
    team_key: str | None = None,
) -> dict[str, Any]:
    cfg = seeds_cfg or load_seeds_config()
    thresholds = cfg.get("proposal_thresholds") or {}
    min_pages = int(thresholds.get("min_pages_per_module") or 5)
    min_branch_pages = int(thresholds.get("min_wiki_branch_pages") or 8)

    seeds = parse_module_seeds(cfg, team=team_key)
    noise_patterns = _compile_keywords(
        [str(x) for x in (cfg.get("engineering_noise_keywords") or []) if str(x).strip()]
    )

    by_seed = assign_pages_to_seeds(pages, seeds)
    seed_props = build_seed_proposals(pages, seeds, by_seed, min_pages=min_pages)

    assigned: set[str] = set()
    for group in by_seed.values():
        for page in group:
            assigned.add(page.page_id)

    branch_props: list[ProposedModule] = []
    if parent_by_child and title_by_id:
        branch_props = propose_wiki_branch_modules(
            pages,
            root_id,
            parent_by_child,
            title_by_id,
            min_branch_pages=min_branch_pages,
            assigned_ids=assigned,
        )

    merged = merge_proposals(seed_props, branch_props)
    for prop in merged:
        assigned.update(prop.page_ids)

    non_business = estimate_non_business(pages, assigned, noise_patterns)

    return {
        "root_id": root_id,
        "team_key": team_key or "",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "method": "wiki-tree + strategy-industry-seeds + facet-signals",
        "strategy_dimensions": cfg.get("strategy_dimensions") or [],
        "page_total": len(pages),
        "proposed_modules": [_proposal_to_dict(p) for p in merged],
        "non_business_estimate": non_business,
        "review_notes": (
            "Script proposes modules only; human must approve slugs and copy cues into "
            "s2-domain-profiles.json before s2_recognize routes pages."
        ),
    }


def _proposal_to_dict(prop: ProposedModule) -> dict[str, Any]:
    return {
        "slug": prop.slug,
        "name_cn": prop.name_cn,
        "axis": prop.axis,
        "source": prop.source,
        "confidence": prop.confidence,
        "page_count": prop.page_count,
        "page_ids": prop.page_ids,
        "sample_titles": prop.sample_titles,
        "wiki_branch": prop.wiki_branch,
        "strategy_dimension_ids": prop.strategy_dimension_ids,
        "facet_counts": prop.facet_counts,
        "suggested_keywords": prop.suggested_keywords,
        "score": prop.score,
        "deliver_target": f"_deliver/{prop.slug}/{prop.slug}-领域知识-工作稿.md",
    }


def render_proposed_modules_md(payload: Mapping[str, Any]) -> str:
    root_id = payload.get("root_id", "")
    lines = [
        f"# S2 模块提议 · 根 `{root_id}`",
        "",
        "> 由 `scripts/distill/s2_propose_modules.py` 生成。**待人工审阅**后再写入 "
        "`s2-domain-profiles.json` 并重跑 `s2_recognize.py`。",
        "",
        f"- 生成时间：`{payload.get('generated_at', '')}`",
        f"- 方法：{payload.get('method', '')}",
        f"- 页面总数：**{payload.get('page_total', 0)}**",
        "",
        "## strategy.md 行业关切（标尺）",
        "",
        "| 维度 ID | 标签 | 典型关切 |",
        "|---------|------|----------|",
    ]
    for row in payload.get("strategy_dimensions") or []:
        lines.append(
            f"| `{row.get('id', '')}` | {row.get('label', '')} | {row.get('concern', '')} |"
        )

    lines.extend(["", "## 提议模块", ""])
    for mod in payload.get("proposed_modules") or []:
        lines.extend(
            [
                f"### {mod.get('name_cn')}（`{mod.get('slug')}`）",
                "",
                f"- **strategy 维度**：{mod.get('axis', '')}",
                f"- **来源**：{mod.get('source')} · **置信度**：{mod.get('confidence')} · **页数**：{mod.get('page_count')}",
                f"- **成稿入口**：`{mod.get('deliver_target', '')}`",
            ]
        )
        if mod.get("wiki_branch"):
            lines.append(f"- **Wiki 分支**：{mod.get('wiki_branch')}")
        if mod.get("strategy_dimension_ids"):
            lines.append(f"- **行业维度 ID**：{', '.join(mod.get('strategy_dimension_ids') or [])}")
        if mod.get("sample_titles"):
            lines.append("- **样例标题**：")
            for title in mod.get("sample_titles") or []:
                lines.append(f"  - {title}")
        if mod.get("suggested_keywords"):
            kw = ", ".join(f"`{k}`" for k in (mod.get("suggested_keywords") or [])[:16])
            lines.append(f"- **建议 domain_cues**：{kw}")
        lines.append("")

    nb = payload.get("non_business_estimate") or {}
    lines.extend(
        [
            "## 非业务估算",
            "",
            f"- 未归入提议模块的页面：**{nb.get('unassigned_page_count', 0)}**",
            f"- 其中工程/协作文档特征：**{nb.get('engineering_noise_count', 0)}**",
        ]
    )
    if nb.get("sample_noise_titles"):
        lines.append("- 样例：")
        for title in nb.get("sample_noise_titles") or []:
            lines.append(f"  - {title}")

    lines.extend(
        [
            "",
            "## 下一步",
            "",
            "1. 审阅上表：合并/拆分/重命名 slug",
            "2. 将确认的模块写入 `domain-knowledge/s2-domain-profiles.json` → `profiles_by_team.<team>`",
            "3. `python3 scripts/distill/s2_recognize.py --root-id "
            f"{root_id}`",
            "4. 在 `DOMAIN_MODULE_CHECKLIST.md` 标 **`确认`** 后 **`继续`** Compose",
            "",
        ]
    )
    return "\n".join(lines)


def render_checklist_draft(payload: Mapping[str, Any]) -> str:
    from runtime.checklist_modules import render_checklist_header, render_module_block

    root_id = payload.get("root_id", "")
    lines = render_checklist_header(
        str(root_id),
        purpose_lines=[
            "本文件由 S2 模块提议脚本生成，**全部为 `待确认`**。",
            "审阅后复制到 `DOMAIN_MODULE_CHECKLIST.md` 或手动合并模块块。",
            "窄屏友好：每个模块一块；通常只需改 **状态**。",
        ],
    )
    for mod in payload.get("proposed_modules") or []:
        slug = mod.get("slug", "")
        name = mod.get("name_cn", slug)
        axis = mod.get("axis", "")
        facets = ", ".join(f"`{k}`" for k in sorted((mod.get("facet_counts") or {}).keys()))
        scan = facets or "（待 S2 扫描）"
        target = mod.get("deliver_target") or f"_deliver/{slug}/{slug}-领域知识-工作稿.md"
        note = f"S2 propose · {mod.get('confidence')} · {mod.get('page_count')} pages"
        lines.extend(
            render_module_block(
                theme=str(name),
                slug=str(slug) if slug else None,
                axis=str(axis),
                scan_dirs=scan,
                main_entry=str(target),
                status="待确认",
                note=note,
            )
        )
    lines.extend(
        render_module_block(
            theme="非业务/工程资料",
            slug=None,
            axis="非领域或待后续判定",
            scan_dirs="`facet-gateway/`、`facet-misc/`、`facet-unmatched/`",
            main_entry="_附录/非业务/非业务资料索引.md",
            status="不归档",
            note="不进入成稿主线",
        )
    )
    return "\n".join(lines).rstrip() + "\n"


def build_parent_map_bfs(
    *,
    root_id: str,
    iter_children: Callable[[str], Iterable[Mapping[str, Any]]],
) -> tuple[dict[str, str | None], dict[str, list[str]], dict[str, str]]:
    parent_by_child: dict[str, str | None] = {root_id: None}
    children_by_parent: dict[str, list[str]] = defaultdict(list)
    title_by_id: dict[str, str] = {root_id: root_id}

    queue: list[str] = [root_id]
    seen: set[str] = {root_id}
    while queue:
        parent_id = queue.pop(0)
        for child in iter_children(parent_id):
            cid = str(child.get("id") or "").strip()
            if not cid or cid in seen:
                continue
            seen.add(cid)
            parent_by_child[cid] = parent_id
            children_by_parent[parent_id].append(cid)
            title_by_id[cid] = str(child.get("title") or cid).strip()
            queue.append(cid)

    return parent_by_child, dict(children_by_parent), title_by_id
