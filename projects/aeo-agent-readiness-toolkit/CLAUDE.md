# AEO & Agent Readiness Toolkit

This repository contains a reusable toolkit of Agent Skills, not a website.

When asked to audit or optimize a project for AEO or AI agents, start with the
`aeo-agent-readiness` skill; it selects the focused modules that apply.

## Working rules

- Inspect before changing anything.
- Keep local evidence and live evidence separate. A file in the repository is
  never proof that a URL is served.
- Classify applicability honestly: `N/A` is a correct result, not a gap to fill.
- Never publish a capability the site does not have, and never invent a
  specification. When a spec cannot be verified, report `MANUAL REVIEW`.
- Crawler permissions, content-usage policy, DNS, CDN/WAF, deployment, commerce
  and authentication all require an explicit instruction from the owner.

## Commands

```bash
S=.claude/skills/aeo-agent-readiness/scripts
python $S/aeo_audit.py --project . --url https://example.com
python $S/validate_toolkit.py
python $S/test_toolkit.py
```

Run `validate_toolkit.py` and `test_toolkit.py` after any change to the toolkit
itself. Full documentation is in [AEO-TOOLKIT.md](AEO-TOOLKIT.md).
