# Check catalog

Every check, the module that owns it, when it applies, and its default priority.
Priorities escalate on real evidence: a site-wide `Disallow: /` raises
Crawlability to P0, a JavaScript-only homepage raises Server-rendered content to
P0, and a robots/edge contradiction raises Actual bot access to P0.

## Discoverability — `aeo-discoverability`

| Check | Applies when | Default | Score set |
|---|---|---|---|
| robots.txt | Always | P1 | Agent Readiness |
| Sitemap | The site has content | P1 | Agent Readiness |
| HTTP Link headers | A live origin is supplied | P2 | Agent Readiness |
| DNS-AID | Always reported as diagnostics | P3 | Agent Readiness |

## Content Accessibility — `aeo-content-accessibility`

| Check | Applies when | Default | Score set |
|---|---|---|---|
| Markdown negotiation | A live origin is supplied | P2 | Agent Readiness |
| Server-rendered content | HTML exists | P0 when JS-only, else P2 | AEO Technical |
| Semantic HTML | HTML exists | P1 | AEO Technical |

## Bot Access — `aeo-bot-access`

| Check | Applies when | Default | Score set |
|---|---|---|---|
| AI Bot Rules | Always | P1 | Agent Readiness |
| Actual bot access | A live origin is supplied | P0 on contradiction, else P2 | Agent Readiness |
| Content Signals | Always | P2 | Agent Readiness |
| Web Bot Auth | Always reported as compatibility | P3 | Agent Readiness |

## Protocol Discovery — `aeo-protocol-discovery`

| Check | Applies when | Default | Score set |
|---|---|---|---|
| API Catalog | An HTTP API exists | P2 | Agent Readiness |
| OAuth discovery | OAuth is implemented | P2 | Agent Readiness |
| OAuth Protected Resource | A protected resource server exists | P2 | Agent Readiness |
| Auth.md | An auth surface exists | P3 | Agent Readiness |
| MCP Server Card | An MCP server is served | P3 | Agent Readiness |
| A2A Agent Card | An agent service is exposed | P3 | Agent Readiness |
| Agent Skills | Real agent-executable capabilities exist, or an index is already published | P1 | Agent Readiness |
| WebMCP | In-page agent tools exist | P3 | Agent Readiness |
| ARD Manifest | ARD capability exists | P3 | Agent Readiness |

Everything in this section is `N/A` when its capability is absent. A published
endpoint is always audited, even when the local scan found no capability — it is
already a public claim.

## Commerce — `aeo-commerce-readiness`

| Check | Applies when | Default | Score set |
|---|---|---|---|
| x402, MPP, UCP, ACP | A payment dependency or transaction code exists | P3, `MANUAL REVIEW` | Agent Readiness |

A `/pricing` page is not commerce. Absent commerce means all four are `N/A`.

## AEO — `aeo-answerability`

| Check | Applies when | Default | Score set |
|---|---|---|---|
| Crawlability | Always | P0 when blocked, else P1 | AEO Technical |
| Content availability | HTML exists | P1 | AEO Technical |
| Entity clarity | HTML exists | P1 | AEO Technical |
| Structured data | HTML exists | P1 | AEO Technical |
| Answer extraction | HTML exists | P1 | AEO Technical |
| Citation readiness | HTML exists | P1 | AEO Technical |
| Canonicalization | HTML exists | P1 | AEO Technical |
| Content duplication | Several documents exist | P2 | AEO Technical |

## Availability

| Check | Applies when | Default | Score set |
|---|---|---|---|
| Homepage availability | A live origin is supplied | P0 | Agent Readiness |
| llms.txt | Always, as an optional enhancement | P2 | Agent Readiness |

## Evidence layers

Each check records `local_evidence` and `live_evidence` separately. Live evidence
supersedes local evidence, and local evidence is kept as context. A local file is
never reported as a published file: local-only conclusions say so in the detail
text.
