---
name: aeo-agent-readiness
description: Orchestrate a complete AEO and AI Agent Readiness audit of a local web project and, when a URL is supplied, its live origin. Use when asked to audit this website for AEO, optimize this project for AI agents, make this website agent-ready, analyze AI discoverability, improve Answer Engine Optimization, check a site against isitagentready, or audit machine-readable AI discovery.
---

# AEO & Agent Readiness Orchestrator

Entry point for the toolkit. Detect the stack, decide what actually applies, run
the audit, prioritise, implement only safe fixes, validate, and report.

The goal is that an agent can **discover → access → parse → understand → cite →
interact → transact** with the site, but only for capabilities the site really
has.

## The rule that overrides everything

Never create a false signal. Do not publish an MCP Server Card, OAuth discovery
document, API endpoint, WebMCP tool, commerce protocol declaration or Agent
Skills index unless the underlying capability genuinely exists and works.

A check that does not apply is `N/A`, never `FAIL`. If a specification cannot be
verified against primary documentation, do not implement it: report
`MANUAL REVIEW — manual verification required`.

## Workflow

### 1. Inspect before touching anything

```bash
python .claude/skills/aeo-agent-readiness/scripts/aeo_audit.py --project . --json-only
```

Read `meta.stack`, `meta.site_type` and `meta.capabilities` first. The audit
classifies the project as `Content Site`, `API / Application`, `Hybrid` or
`Unknown` from real evidence, and records why each capability was or was not
found. If a classification looks wrong, inspect the repository yourself and say
so in the report rather than silently overriding it.

### 2. Run the full audit

```bash
# Local evidence only
python .claude/skills/aeo-agent-readiness/scripts/aeo_audit.py --project .

# Local + live evidence, which is what an agent actually receives
python .claude/skills/aeo-agent-readiness/scripts/aeo_audit.py --project . --url https://example.com
```

`public/robots.txt` existing in the repository is **not** evidence that
`https://example.com/robots.txt` returns 200. Without `--url`, every live check
is `MANUAL REVIEW` and is excluded from both scores. Always ask for the public
URL when the user has one.

If TLS verification fails on the auditing machine, the run reports
`MANUAL REVIEW`, not a site failure. `--insecure` exists for diagnostics only and
stamps the report; never present an insecure run as verified.

### 3. Read results per module

Delegate detail work to the focused skills: [aeo-discoverability](../aeo-discoverability/SKILL.md),
[aeo-content-accessibility](../aeo-content-accessibility/SKILL.md),
[aeo-bot-access](../aeo-bot-access/SKILL.md),
[aeo-protocol-discovery](../aeo-protocol-discovery/SKILL.md),
[aeo-commerce-readiness](../aeo-commerce-readiness/SKILL.md),
[aeo-answerability](../aeo-answerability/SKILL.md) and
[aeo-llms](../aeo-llms/SKILL.md). Load a module's SKILL.md when you need to act
on its findings, not before.

### 4. Prioritise

| Priority | Meaning |
|---|---|
| P0 | An agent cannot access, discover or interpret essential content |
| P1 | Significant discoverability, machine-readability or entity-clarity problems |
| P2 | Efficiency and interoperability enhancements |
| P3 | Emerging standards and advanced capabilities |

Never promote a P3 experimental item to P0. See
[references/check-catalog.md](references/check-catalog.md) for every check, its
applicability gate and its default priority.

### 5. Fix only what is safe

Implement P0 and P1 fixes that are local, reversible and provably correct. Before
editing:

1. inspect existing conventions and do not overwrite custom configuration;
2. make the smallest change that resolves the finding;
3. capture a logical backup (`git diff`, or note the prior content when the
   project is not a git repository);
4. re-run the narrowest relevant check, then the full audit.

Do **not**, without an explicit instruction: deploy, edit DNS, change
Cloudflare/WAF/CDN rules, change AI training or content-usage policy, enable
commerce or authentication, or add a capability the site does not have. Leave
P2/P3 changes as recommendations unless the user asks for them.

### 6. Validate and report

```bash
python .claude/skills/aeo-agent-readiness/scripts/validate_toolkit.py
python .claude/skills/aeo-agent-readiness/scripts/test_toolkit.py
```

Re-running the audit rewrites `reports/aeo-agent-readiness-report.md` and
`.json`, preserves the prior JSON as `*.previous.json`, and fills the
Before / After section automatically. Record every modified file and every test
you ran.

## Scoring

Two independent scores over **disjoint** check sets:

- **Agent Readiness** — discovery, access, bot reality, protocol interoperability, commerce.
- **AEO Technical** — crawlability, content availability, semantic structure, entities, structured data, canonicalisation, answer extraction, citation readiness.

```
score = 100 * Σ(weight × status_value) / Σ(weight)
status_value: PASS 1.0 | WARNING 0.5 | FAIL 0.0
excluded entirely: N/A, MANUAL REVIEW
```

`N/A` never lowers a score. A `null` score means nothing in that set produced
scorable evidence — report it as "not scored", never as zero. Full derivation in
[references/scoring.md](references/scoring.md).

## Statuses

`PASS` verified · `FAIL` applicable defect · `WARNING` applicable but incomplete
or unverified · `N/A` not applicable, excluded · `MANUAL REVIEW` no evidence
available here; needs the owner, a deployment, a browser, DNS, or specification
verification.

## Before implementing any emerging standard

Verify the current specification against primary sources listed in
[references/SOURCES.md](references/SOURCES.md). x402, MPP, UCP, ACP, ARD,
DNS-AID, WebMCP, Auth.md and Agent Skills discovery are emerging or pre-1.0.
Never invent a path, JSON schema, header or digest format.
