---
name: aeo-protocol-discovery
description: Audit machine-readable protocol discovery that genuinely applies, covering API catalogs, OAuth authorization server and protected resource metadata, Auth.md, MCP Server Cards, A2A Agent Cards, Agent Skills discovery, WebMCP and ARD manifests. Use when checking well-known endpoints, agent protocol interoperability, or discovery document correctness.
---

# AEO Protocol Discovery

Audit each protocol independently and return `PASS`, `FAIL`, `WARNING`, `N/A` or
`MANUAL REVIEW`.

**Establish the capability before judging the endpoint.** A missing
`/.well-known/mcp.json` is only a defect if the site actually runs an MCP server.
Otherwise it is `N/A`. Publishing a discovery document for a capability that does
not exist is the worst outcome this toolkit can produce: agents will attempt the
capability and fail.

```bash
python scripts/discovery_scan.py https://example.com
```

The scanner reports status, content type, CORS, cache headers, JSON validity, and
`spec_confidence` for each path. HTML returned from a catch-all route is reported
as *not present*, because a 200 from a SPA fallback is not an endpoint.

## Applicability gates

| Check | Applies only when | Specification |
|---|---|---|
| API Catalog | The site exposes an HTTP API | RFC 9727, OpenAPI |
| OAuth discovery | OAuth is actually implemented | RFC 8414, OIDC Discovery |
| OAuth Protected Resource | A resource server is actually protected | RFC 9728 |
| Auth.md | An authentication surface exists | Emerging convention — verify first |
| MCP Server Card | An MCP server is actually served | MCP docs — verify path and schema |
| A2A Agent Card | An agent service is actually exposed | A2A docs — verify first |
| Agent Skills | Real agent-executable capabilities exist | agentskills.io — verify schema |
| WebMCP | In-page agent tools genuinely exist | Verify first |
| ARD Manifest | ARD capability exists | Pre-1.0 — verify first |

Anything marked "verify first" stays `MANUAL REVIEW` until you have checked the
current specification against
[../aeo-agent-readiness/references/SOURCES.md](../aeo-agent-readiness/references/SOURCES.md).
Never invent a path, a JSON schema, a header or a digest format.

## Agent Skills discovery

Only publish when the site really offers those capabilities **to external
agents**. A repository's internal authoring skills are not site capabilities.

```bash
# Preview without writing
python scripts/generate_agent_skills_index.py --skills ./agent-skills --publish-root ./public --dry-run

# Publish index and artifacts together
python scripts/generate_agent_skills_index.py --skills ./agent-skills --publish-root ./public \
    --schema-version <verified-version> --confirm-applicable

# Verify an existing index still matches its artifacts
python scripts/generate_agent_skills_index.py --skills ./agent-skills --publish-root ./public --verify
```

The generator enforces what a hand-written index gets wrong:

- the index and every `SKILL.md` artifact are written **together**, so the index
  can never reference an artifact that is not published;
- every digest is computed from the bytes actually written to the publish root —
  never typed by hand;
- names must be lowercase kebab-case, match their directory, and carry a
  description within the specification's limits;
- publishing requires `--confirm-applicable`.

Each published skill needs a `name`, a `description` and clear instructions, and
should use progressive disclosure — a short `SKILL.md` with detail in
`references/`. Re-run the generator whenever a skill changes, and confirm the
served responses handle `GET` and `HEAD`, use the right content type, and set
cache and CORS headers appropriately.

If an index is already published, verify every referenced artifact resolves. A
broken index is a `FAIL` and should be removed or repaired immediately.

## Reporting

For every `MANUAL REVIEW`, state the specification that must be verified, the
source to verify it against, and what would change the verdict. Do not implement
in the same pass as the audit.
