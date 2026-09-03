# AEO & Agent Readiness Audit

Domain: https://acdamerica.net/
Project: acdamerica.net
Stack: Unknown
Site Type: Unknown
Date: 2026-08-24T15:37:39+00:00
Evidence layers: local+live

> **TLS certificate verification was disabled for this run.** Live results are diagnostics only.

Agent Readiness Score: 91/100  
  applicable 10 | passed 8 | warnings 2 | failed 0 | N/A 12 | manual review 2

AEO Technical Score: 100/100  
  applicable 9 | passed 9 | warnings 0 | failed 0 | N/A 0 | manual review 1

## Executive Summary

The audit ran 34 checks: 17 PASS, 2 WARNING, 0 FAIL, 12 N/A, 3 MANUAL REVIEW.

Findings by priority: P0 0, P1 0, P2 3, P3 2.

Scoring method: score = 100 * sum(weight * status_value) / sum(weight) over checks whose status is PASS (1.0), WARNING (0.5) or FAIL (0.0). N/A and MANUAL REVIEW are excluded from both numerator and denominator. The two scores use disjoint check sets. A score of null means no check in that set produced scorable evidence.

## P0 Blocking Issues

_An agent cannot access, discover or interpret essential content._

None identified.

## P1 High Impact

_Significant discoverability, machine-readability or entity-clarity problems._

None identified.

## P2 Enhancements

_Improvements to efficiency or interoperability._

- **AI Bot Rules** (WARNING, Bot Access): No AI-crawler-specific rules are served; the wildcard group applies
- **API Catalog** (WARNING, Protocol Discovery): Capability exists but nothing is published at /.well-known/api-catalog, /openapi.json
- **Content duplication** (MANUAL REVIEW, AEO): No local source supplied; judged from the live origin only

## P3 Experimental

_Emerging standards and advanced capabilities. Never treated as blocking._

- **DNS-AID** (MANUAL REVIEW, Discoverability): DNS-AID requires a DNS record this toolkit never creates. Verify the current specification, then hand the record name, value and verification procedure to the DNS owner
  - Recommendation: Diagnostics only. See references/dns-aid.md for the reporting template
- **Web Bot Auth** (MANUAL REVIEW, Bot Access): No verified signature exchange observed. Web Bot Auth is a property of the requesting agent and the origin's verification policy; never fabricate cryptographic material

## Discoverability

| Check | Status | Score set | Evidence | Detail |
|---|---|---|---|---|
| robots.txt | PASS | Agent Readiness | live | Served robots.txt is valid and references 1 sitemap(s) |
| Sitemap | PASS | Agent Readiness | live | Sitemap valid, referenced from robots.txt, 328 URLs, sample all 2xx |
| HTTP Link headers | PASS | Agent Readiness | live | Link header advertises: describedby |
| DNS-AID | MANUAL REVIEW | Agent Readiness | none | DNS-AID requires a DNS record this toolkit never creates. Verify the current specification, then hand the record name, value and verification procedure to the DNS owner |

## Content Accessibility

| Check | Status | Score set | Evidence | Detail |
|---|---|---|---|---|
| Markdown negotiation | PASS | Agent Readiness | live | Served text/markdown with Markdown structure |
| Server-rendered content | PASS | AEO Technical | live | Homepage delivers 11972 characters of text without JavaScript |
| Semantic HTML | PASS | AEO Technical | live | Served homepage uses landmarks and a coherent heading structure |

## Bot Access

| Check | Status | Score set | Evidence | Detail |
|---|---|---|---|---|
| AI Bot Rules | WARNING | Agent Readiness | live | No AI-crawler-specific rules are served; the wildcard group applies |
| Actual bot access | PASS | Agent Readiness | live | Declared and actual access agree. Content served to: GPTBot, ClaudeBot, PerplexityBot, Googlebot, Bingbot |
| Content Signals | PASS | Agent Readiness | live | Content signals served: search=yes, ai-input=yes, ai-train=no |
| Web Bot Auth | MANUAL REVIEW | Agent Readiness | live | No verified signature exchange observed. Web Bot Auth is a property of the requesting agent and the origin's verification policy; never fabricate cryptographic material |

## Protocol Discovery

| Check | Status | Score set | Evidence | Detail |
|---|---|---|---|---|
| API Catalog | WARNING | Agent Readiness | live | Capability exists but nothing is published at /.well-known/api-catalog, /openapi.json |
| OAuth discovery | N/A | Agent Readiness | none | Not applicable: no OAuth implementation detected; publishing discovery metadata would be a false signal |
| OAuth Protected Resource | N/A | Agent Readiness | none | Not applicable: no OAuth-protected resource detected |
| Auth.md | N/A | Agent Readiness | none | Not applicable: no authentication surface detected |
| MCP Server Card | N/A | Agent Readiness | none | Not applicable: this site does not expose an MCP server |
| A2A Agent Card | N/A | Agent Readiness | none | Not applicable: this site does not expose an agent service |
| Agent Skills | N/A | Agent Readiness | none | Not applicable: no agent-executable capabilities are offered by this site |
| WebMCP | N/A | Agent Readiness | none | Not applicable: no in-page agent tools detected |
| ARD Manifest | N/A | Agent Readiness | none | Not applicable: ARD is pre-1.0 and no ARD capability was detected |

## Commerce

| Check | Status | Score set | Evidence | Detail |
|---|---|---|---|---|
| x402 | N/A | Agent Readiness | none | Not applicable: no local source supplied and no commerce capability observed live |
| MPP | N/A | Agent Readiness | none | Not applicable: no local source supplied and no commerce capability observed live |
| UCP | N/A | Agent Readiness | none | Not applicable: no local source supplied and no commerce capability observed live |
| ACP | N/A | Agent Readiness | none | Not applicable: no local source supplied and no commerce capability observed live |

## AEO

| Check | Status | Score set | Evidence | Detail |
|---|---|---|---|---|
| Crawlability | PASS | AEO Technical | live | Homepage crawlable by general crawlers |
| Content availability | PASS | AEO Technical | live | Served homepage carries 1804 words of extractable text |
| Entity clarity | PASS | AEO Technical | live | Homepage entities: Organization, PostalAddress, WebSite |
| Structured data | PASS | AEO Technical | live | Served JSON-LD parses and matches visible content |
| Answer extraction | PASS | AEO Technical | live | Homepage exposes a summary and a coherent heading outline |
| Citation readiness | PASS | AEO Technical | live | Homepage carries the signals needed to attribute it |
| Canonicalization | PASS | AEO Technical | live | Canonical declared: https://acdamerica.net/ |
| Content duplication | MANUAL REVIEW | AEO Technical | none | No local source supplied; judged from the live origin only |

## Availability

| Check | Status | Score set | Evidence | Detail |
|---|---|---|---|---|
| Homepage availability | PASS | Agent Readiness | live | HTTP 200 after 0 redirect(s) |
| llms.txt | PASS | Agent Readiness | live | llms.txt served as text/plain |

## Files Modified

None. This run is read-only: it inspects and reports, it does not edit the site.

## Tests Executed

- Local repository inspection (3 files scanned)
- Live origin inspection of https://acdamerica.net/ (TLS verification DISABLED)

## Before / After

| Item | Before | After |
|---|---|---|
| Agent Readiness Score | 91/100 | 91/100 |
| AEO Technical Score | 95/100 | 100/100 |
| Entity clarity | WARNING | PASS |

## Remaining Manual Actions

- **DNS-AID**: DNS-AID requires a DNS record this toolkit never creates. Verify the current specification, then hand the record name, value and verification procedure to the DNS owner
- **Web Bot Auth**: No verified signature exchange observed. Web Bot Auth is a property of the requesting agent and the origin's verification policy; never fabricate cryptographic material
- **Content duplication**: No local source supplied; judged from the live origin only

Owner decisions this toolkit will not make automatically: AI training and retrieval policy, DNS records, CDN/WAF rules, deployment, payment protocols, authentication, and any capability the site does not actually provide.

## Status Legend

| Status | Meaning |
|---|---|
| PASS | verified evidence |
| FAIL | applicable defect |
| WARNING | applicable but incomplete or unverified end to end |
| N/A | not applicable; excluded from scoring |
| MANUAL REVIEW | no evidence available here; needs owner, deployment, browser, DNS or specification verification |

