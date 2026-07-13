---
name: Bug report
about: Report a script failure, test regression, or pack layout issue
title: "[bug] "
labels: bug
---

## Summary

What broke? One or two sentences.

## Steps to reproduce

1.
2.
3.

## Expected behavior


## Actual behavior

Include gate output or stack trace in a fenced block if applicable.

```
(paste here)
```

## Environment

- OS:
- Python version (`python3 --version`):
- Branch / commit:
- Cursor or other harness (if relevant):

## Offline demo check

Does this reproduce with `@requirement-risk DEMO-1 team=demo` or `python3 scripts/verify_skills_pack.py`?

- [ ] Yes — offline repro
- [ ] No — needs Atlassian / tenant config
- [ ] Not tried

## Additional context

No secrets, `.env` contents, or production wiki/Jira exports in this issue.
