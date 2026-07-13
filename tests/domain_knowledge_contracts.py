"""
SSOT constants for domain-knowledge / docs layout contract tests.

Update here first (TDD), then change product code — never duplicate lists in test modules.
"""

from __future__ import annotations

LEGACY_DOMAIN_KNOWLEDGE_DOCS: tuple[str, ...] = (
    "domain-knowledge/00-onboarding.md",
    "domain-knowledge/ACCEPTANCE_CHECKLIST.template.md",
    "domain-knowledge/guide.md",
    "domain-knowledge/jira-pipeline.md",
    "domain-knowledge/coverage-distill-exclude.txt",
)

LEGACY_DOMAIN_KNOWLEDGE_DIRS: tuple[str, ...] = (
    "domain-knowledge/rules",
    "domain-knowledge/rules-distilled",
    "domain-knowledge/context",
    "domain-knowledge/scope",
    "domain-knowledge/gaps",
    "domain-knowledge/materialized/domain",
)

REQUIRED_DOMAIN_KNOWLEDGE_DOCS: tuple[str, ...] = (
    "domain-knowledge/README.md",
    "domain-knowledge/strategy.md",
    "domain-knowledge/strategy.zh-CN.md",
    "domain-knowledge/distill-quality-bar.md",
    "domain-knowledge/distill-quality-bar.zh-CN.md",
    "domain-knowledge/distill-authoring-contract.md",
    "domain-knowledge/distill-authoring-contract.zh-CN.md",
    "domain-knowledge/distill-document-skeleton.md",
    "domain-knowledge/distill-document-skeleton.zh-CN.md",
    "domain-knowledge/DOMAIN_MODULE_CHECKLIST.template.md",
    "domain-knowledge/DOMAIN_MODULE_CHECKLIST.template.zh-CN.md",
    "domain-knowledge/language/glossary.md",
    "domain-knowledge/language/s6-reader-language-policy.json",
    "domain-knowledge/jira/README.md",
    "domain-knowledge/materialized/README.md",
    "domain-knowledge/materialized/_TEMPLATE.md",
    "domain-knowledge/jira/team-roots.json",
)

LEGACY_SCRIPT_FILES: tuple[str, ...] = (
    "scripts/generate_domain_knowledge_from_page.py",
    "scripts/run_distill_release_gate.py",
    "scripts/distill/release_gate.py",
    "scripts/distill/rerun_s2_s5.py",
    "scripts/publish_deliver_to_confluence.py",
    "scripts/publish_glossary_to_confluence.py",
    "scripts/publish_share_page_to_confluence.py",
    "scripts/publish_bc_deliver_to_confluence.py",
    "scripts/publish_cma_deliver_to_confluence.py",
    "scripts/publish_wc_deliver_to_confluence.py",
    "scripts/_tools/update_doc_script_paths.py",
)

LEGACY_WIKI_SKILL_DOC_PATHS: tuple[str, ...] = (
    ".cursor/skills/generate-knowledge-from-wiki/POST-DELIVER-INTRO.md",
)

FORBIDDEN_DOC_TOKENS: tuple[str, ...] = (
    "domain-knowledge/guide.md",
    "domain-knowledge/jira-pipeline.md",
    "coverage-distill-exclude.txt",
    "check_rules_distilled_coverage.py",
    "check_rules_distilled_quality.py",
    "check_rules_distilled_domain_layout.py",
    "domain-knowledge/rules/",
    "domain-knowledge/rules-distilled/",
    "fetch_jira_tickets.py",
    "attribute_jira_tickets.py",
    "publish_deliver_to_confluence.py",
    "publish_glossary_to_confluence.py",
    "publish_share_page_to_confluence.py",
    "publish_bc_deliver_to_confluence.py",
    "publish_cma_deliver_to_confluence.py",
    "publish_wc_deliver_to_confluence.py",
)

DOC_PATHS_FOR_LEGACY_SCAN: tuple[str, ...] = (
    "domain-knowledge/README.md",
    "domain-knowledge/strategy.md",
    "domain-knowledge/distill-quality-bar.md",
    "TEAM_KNOWLEDGE_BASE.md",
    ".cursor/skills/add-knowledge-from-jira/SKILL.md",
    "scripts/README.md",
    "scripts/ARCHITECTURE.md",
)

# Git index must not resurrect removed domain-knowledge paths (dirs + deleted docs).
GIT_UNTRACKED_LEGACY_PATHS: tuple[str, ...] = (
    "domain-knowledge/rules",
    "domain-knowledge/rules-distilled",
    *LEGACY_DOMAIN_KNOWLEDGE_DOCS,
)

# Scripts-only removals (domain-knowledge layout covered by LEGACY_* above).
LEGACY_SCRIPT_FILES_EXTRA: tuple[str, ...] = (
    "scripts/run_bc_jira_sprint_fetch.sh",
    "scripts/jira_full_fetch_loop.sh",
    "scripts/_tools/md_share_to_html.py",
    "scripts/migrate_domain_knowledge_naming.py",
    "scripts/wiki/lib/domain_template_classify.py",
    "scripts/wiki/lib/_paths.py",
    "scripts/distill/order_quality.py",
    "scripts/distill/s5_translation_guard.py",
    "scripts/distill/semantic_quality.py",
    "scripts/distill/decision_quality.py",
    "scripts/distill/s2_quality.py",
    "scripts/distill/proposition_miss_audit.py",
    "scripts/package_risk_split_tier1.sh",
    "docs/分享给同事.md",
    "scripts/teams/cma_deliver_paths.py",
    "scripts/teams/bc_deliver_paths.py",
    "scripts/teams/wc_deliver_paths.py",
)

REMOVED_SCRIPT_COMPAT_DIRS: tuple[str, ...] = (
    "scripts/_tools",
    "scripts/wiki/cli",
    "scripts/wiki/imports",
    "scripts/jira/cli",
    "scripts/jira/imports",
    "scripts/jira/d1",
    "scripts/distill/cli",
    "scripts/teams/cli",
    "scripts/publish",
    "scripts/publish/imports",
    "scripts/archive",
)

# jira must use runtime/ shared kernel — not wiki.lib (Clean Architecture dependency rule).
FORBIDDEN_JIRA_IMPORT_PREFIXES: tuple[str, ...] = (
    "from wiki.lib",
    "from wiki.sync",
    "import wiki.lib",
)

# Active scripts/ naming — Beck "Intention-Revealing Names".
ACTIVE_SCRIPTS_DIR = "scripts"

FORBIDDEN_ACTIVE_SCRIPT_LINE_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"^\s*REPO\s*=\s*REPO_ROOT\s*$", "use REPO_ROOT directly; do not alias REPO"),
    (r"^\s*ROOT\s*=\s*REPO_ROOT\s*$", "use REPO_ROOT directly; do not alias ROOT"),
    (r"^\s*REPO\s*=\s*Path\(", "import REPO_ROOT from runtime.paths"),
    (r"REPO_ROOT\s+as\s+REPO\b", "import REPO_ROOT without alias"),
    (r"\bap\s*=\s*argparse\.ArgumentParser", "name CLI parser `parser`, not `ap`"),
)

FORBIDDEN_ACTIVE_SCRIPT_SYMBOLS: tuple[str, ...] = (
    "get_page_v2",
    "process_page_attachments",
    "save_json",
)

# Short locals that must not reappear once renamed (relative to scripts/).
FORBIDDEN_SHORT_LOCAL_SNIPPETS: tuple[tuple[str, str], ...] = (
    ("jira/lib/jira_team_config.py", 'j = team["jira"]'),
    ("jira/lib/jira_sprints.py", 'j = team["jira"]'),
    ("wiki/steps/materialize.py", "w, sk = materialize"),
    ("wiki/steps/materialize.py", "ko = fm.get"),
    ("jira/steps/attribute.py", "th = d.get"),
    ("domain_check.py", "rc = _distill_checks"),
)

# Step-level *_run / *_types live under <pipeline>/steps/ (not package root).
REQUIRED_STEP_RUN_FILES: tuple[str, ...] = (
    "scripts/wiki/steps/enumerate_run.py",
    "scripts/wiki/steps/extract_run.py",
    "scripts/wiki/steps/materialize_run.py",
    "scripts/jira/steps/fetch_run.py",
    "scripts/jira/steps/fetch_types.py",
    "scripts/jira/steps/attribute_run.py",
    "scripts/jira/steps/attribute_types.py",
    "scripts/jira/steps/check_pipeline_run.py",
    "scripts/jira/steps/check_pipeline_types.py",
    "scripts/jira/steps/read_business_run.py",
    "scripts/jira/steps/read_business_types.py",
    "scripts/jira/steps/materialize_run.py",
    "scripts/jira/steps/materialize_types.py",
    "scripts/wiki/steps/source_coverage_run.py",
)

FORBIDDEN_STEP_RUN_OUTSIDE_STEPS: tuple[str, ...] = (
    "scripts/jira/fetch_run.py",
    "scripts/jira/fetch_types.py",
    "scripts/jira/attribute_run.py",
    "scripts/jira/attribute_types.py",
    "scripts/wiki/sync/enumerate_run.py",
    "scripts/wiki/sync/extract_run.py",
)
