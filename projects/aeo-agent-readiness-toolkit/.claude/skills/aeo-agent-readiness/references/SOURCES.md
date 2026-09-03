# Verification sources

Verify a specification against its primary source before implementing anything
that depends on it. Record the URL and the date you checked in the audit report.

## Stable, safe to implement against

| Topic | Source |
|---|---|
| robots.txt (REP) | RFC 9309 — https://www.rfc-editor.org/rfc/rfc9309.html |
| Sitemaps | https://www.sitemaps.org/protocol.html |
| Web Linking (`Link` header) | RFC 8288 — https://www.rfc-editor.org/rfc/rfc8288.html |
| OAuth Authorization Server Metadata | RFC 8414 — https://www.rfc-editor.org/rfc/rfc8414.html |
| OAuth Protected Resource Metadata | RFC 9728 — https://www.rfc-editor.org/rfc/rfc9728.html |
| API Catalog | RFC 9727 — https://www.rfc-editor.org/rfc/rfc9727.html |
| security.txt | RFC 9116 — https://www.rfc-editor.org/rfc/rfc9116.html |
| `.well-known` registry | https://www.iana.org/assignments/well-known-uris/ |
| Structured data vocabulary | https://schema.org/ |
| OpenAPI | https://spec.openapis.org/ |

## Emerging, version-sensitive or pre-1.0 — verify before every use

| Topic | Source | Status |
|---|---|---|
| Agent readiness criteria | https://isitagentready.com/ | Evolving checklist |
| Cloudflare agent and crawler guidance | https://developers.cloudflare.com/ | Vendor documentation |
| Agent Skills | https://agentskills.io/ | Discovery schema evolving |
| Model Context Protocol | https://modelcontextprotocol.io/ | Server Card path and schema evolving |
| A2A | https://a2a-protocol.org/ | Agent Card schema evolving |
| WebMCP | https://webmachinelearning.github.io/webmcp/ | Draft |
| llms.txt | https://llmstxt.org/ | Community proposal |
| Content Signals | Cloudflare documentation | Emerging |
| Web Bot Auth | IETF drafts | Draft |
| x402, MPP, UCP, ACP | Respective official specifications | Emerging / pre-1.0 |
| ARD | Proposal | Pre-1.0 |
| DNS-AID | Proposal | Pre-1.0 |

## The rule

If a specification cannot be verified with enough certainty, **DO NOT IMPLEMENT**.
Report it as `MANUAL REVIEW — manual verification required`, name the source that
must be checked, and state what would change the verdict.

Never invent syntax, paths, JSON schemas, HTTP headers, digest formats or naming
conventions. A plausible-looking discovery document that does not match the real
specification is worse than no document at all: agents will parse it, act on it,
and fail.
