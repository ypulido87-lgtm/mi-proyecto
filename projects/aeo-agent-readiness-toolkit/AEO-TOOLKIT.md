# AEO & Agent Readiness Toolkit

A modular set of Claude Code Agent Skills that audits a web project — and its
live origin — for Answer Engine Optimization and AI Agent Readiness, then
implements only the fixes that are safe and genuinely applicable.

The goal is a site that agents can really use across
**discover → access → parse → understand → cite → interact → transact**, not a
higher number on any scorecard.

## The rule that overrides everything

**Never create a false signal.** The toolkit will not publish an MCP Server Card,
OAuth discovery document, API endpoint, WebMCP tool, commerce protocol
declaration or Agent Skills index unless the capability genuinely exists.

A check that does not apply is `N/A`, never `FAIL`, and `N/A` never lowers a
score. When a specification cannot be verified against primary documentation, the
toolkit reports `MANUAL REVIEW — manual verification required` and implements
nothing.

## AEO vs Agent Readiness

They are related but distinct, so the toolkit scores them separately over
disjoint check sets and never averages them.

| | Agent Readiness | AEO Technical |
|---|---|---|
| Question | Can an agent discover, reach and interoperate with the site? | Can an answer engine parse, understand and cite the content? |
| Covers | robots, sitemap, Link headers, DNS-AID, real bot access, content signals, Markdown negotiation, llms.txt, protocol discovery, commerce | crawlability, content availability, server-rendered content, semantic HTML, structured data, entities, canonicalization, answer extraction, citation readiness, duplication |
| Fails when | An agent is blocked, or a published capability does not work | Content is unreadable, unattributable, or its markup is unsupported by the page |

A site can be perfectly agent-accessible and still be uncitable, and vice versa.

## Architecture

```
.claude/skills/
├── aeo-agent-readiness/        orchestrator + shared engine
│   ├── scripts/aeo_audit.py    the audit runner
│   ├── scripts/aeolib/         fetch, project, checks, scoring, report
│   ├── scripts/validate_toolkit.py
│   ├── scripts/test_toolkit.py
│   ├── references/             SOURCES, scoring model, check catalog
│   └── assets/report-template.md
├── aeo-discoverability/        robots_parser, sitemap_validator, http_inspect
├── aeo-content-accessibility/  markdown_negotiation, semantic_html
├── aeo-bot-access/             bot_access
├── aeo-protocol-discovery/     discovery_scan, generate_agent_skills_index
├── aeo-commerce-readiness/     commerce_protocols
├── aeo-answerability/          structured_data
└── aeo-llms/                   llms_txt
```

Every skill owns its own tools. The engine in the orchestrator loads them by name
through `aeolib.paths.load_skill_script`, so each tool stays independently
runnable and there is exactly one implementation of each check.

Everything lives under `.claude/skills/`, which makes the toolkit portable: copy
that directory into any repository and it works there. A test asserts this.

Python 3.10+, standard library only. No install step, no network dependency.

## Using it

Say this to Claude Code:

> Audit and optimize this website for AEO and AI Agent Readiness. Use the
> complete AEO toolkit, detect which checks are applicable, implement safe P0/P1
> fixes, validate the changes and generate a before/after report.

Other phrasings that select the toolkit: *audit this website for AEO*, *optimize
this project for AI agents*, *make this website agent-ready*, *analyze AI
discoverability*, *improve Answer Engine Optimization*, *check this site against
isitagentready*, *audit machine-readable AI discovery*.

Directly:

```bash
S=.claude/skills/aeo-agent-readiness/scripts

python $S/aeo_audit.py --project .                              # local evidence
python $S/aeo_audit.py --project . --url https://example.com    # local + live
python $S/aeo_audit.py --project . --json-only                  # JSON to stdout
python $S/validate_toolkit.py                                   # validate skills
python $S/test_toolkit.py                                       # 100 offline assertions
```

Individual tools:

```bash
python .claude/skills/aeo-discoverability/scripts/robots_parser.py https://example.com/robots.txt
python .claude/skills/aeo-discoverability/scripts/sitemap_validator.py https://example.com/sitemap.xml --check-urls 25
python .claude/skills/aeo-content-accessibility/scripts/semantic_html.py https://example.com
python .claude/skills/aeo-answerability/scripts/structured_data.py https://example.com
python .claude/skills/aeo-bot-access/scripts/bot_access.py https://example.com
python .claude/skills/aeo-protocol-discovery/scripts/discovery_scan.py https://example.com
python .claude/skills/aeo-llms/scripts/llms_txt.py audit ./public/llms.txt
```

## Local and live evidence

The toolkit works in two layers and keeps them separate on every check.

- **LOCAL** — configuration, routes, middleware, public directories, metadata,
  generated files, server configuration.
- **LIVE** — what an agent actually receives, when a URL is supplied.

`public/robots.txt` existing in the repository is **not** evidence that
`https://domain.com/robots.txt` returns 200. Without `--url`, live-only checks are
`MANUAL REVIEW` and are excluded from scoring rather than counted as failures.
Always supply the public URL when one exists.

If TLS verification fails on the auditing machine (a proxy, or a stale trust
store), the run reports `MANUAL REVIEW`, not a site outage. `--insecure` exists
for diagnostics only and stamps the report.

## Reading the results

| Status | Meaning | Scored |
|---|---|---|
| `PASS` | Verified evidence | Yes, 1.0 |
| `WARNING` | Applicable but incomplete or unverified end to end | Yes, 0.5 |
| `FAIL` | Applicable defect | Yes, 0.0 |
| `N/A` | Not applicable — the capability does not exist | No |
| `MANUAL REVIEW` | No evidence here; needs an owner, deployment, browser, DNS or spec check | No |

```
score = 100 * sum(weight * status_value) / sum(weight)
```

A `null` score means nothing in that set produced scorable evidence. It is "not
scored", never zero. Full model in
[scoring.md](.claude/skills/aeo-agent-readiness/references/scoring.md).

Priorities: **P0** an agent cannot access or interpret essential content · **P1**
significant discoverability or entity-clarity problems · **P2** enhancements ·
**P3** experimental. P3 is never escalated to P0.

## What needs your approval

The toolkit inspects and reports freely. It will implement safe, local, reversible
P0/P1 fixes. It will **not** do any of the following unless you ask explicitly:

- change AI crawler permissions or content-usage policy (`search`, `ai-input`,
  `ai-train`) — these are legal statements about your content;
- edit DNS records;
- change Cloudflare, WAF or CDN configuration;
- deploy anything;
- enable commerce, payments or authentication;
- publish a discovery document for a capability that does not exist;
- rewrite, merge or delete content;
- apply P2/P3 changes.

## Reports

Each run writes to `reports/` in the audited project:

- `aeo-agent-readiness-report.md`
- `aeo-agent-readiness-report.json`
- `aeo-agent-readiness-report.previous.json` (the superseded run)

Because the previous run is retained, re-running the audit fills the
**Before / After** section automatically — that is the intended workflow:

```bash
python $S/aeo_audit.py --project . --url https://example.com   # baseline
# ...apply approved fixes...
python $S/aeo_audit.py --project . --url https://example.com   # before/after populated
```

## Reusing it in another project

```bash
cp -r .claude/skills /path/to/other-project/.claude/
cd /path/to/other-project
python .claude/skills/aeo-agent-readiness/scripts/aeo_audit.py --project . --url https://thatsite.com
```

Nothing in the toolkit is specific to this repository, and the test suite verifies
that it runs correctly from a copied location.

## Verifying emerging standards

x402, MPP, UCP, ACP, ARD, DNS-AID, WebMCP, Auth.md and Agent Skills discovery are
emerging or pre-1.0. Verify each against
[SOURCES.md](.claude/skills/aeo-agent-readiness/references/SOURCES.md) before
implementing anything. Never invent a path, schema, header or digest format — a
plausible-looking discovery document that does not match the real specification is
worse than none, because agents will parse it, act on it, and fail.
