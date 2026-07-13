# Glossary

Shared terminology for agents and humans. Keep this file **project-specific**.

## How to use

1. Add terms your domain experts actually say.
2. Prefer `中文术语（English Term）` when bilingual briefs are enabled.
3. After S6, `scripts/distill/glossary_update.py` can refresh auto sections from briefs.

## Seed examples (replace)

### Domain brief

- **Definition**: An adjudicated, reader-facing knowledge product for one domain module (`*-领域知识定稿.md` / `*-domain-brief.md`).
- **Source**: This repository’s distill pipeline (S6).

### Confirmation gate

- **Definition**: Human approval of module boundaries on `DOMAIN_MODULE_CHECKLIST.md` before Compose (S3→S6).
- **Source**: Wiki RUNBOOK.
