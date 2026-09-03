# AEO & Agent Readiness Audit

Domain: https://pulidotax.com/
Project: sitio-pulidotax
Stack: Static HTML | hosting: Apache
Site Type: Content Site
Date: 2026-09-03T18:20:58+00:00
Evidence layers: local+live

Agent Readiness Score: 97/100  
  applicable 9 | passed 8 | warnings 1 | failed 0 | N/A 13 | manual review 2

AEO Technical Score: 90/100  
  applicable 10 | passed 8 | warnings 2 | failed 0 | N/A 0 | manual review 0

## Executive Summary

The audit ran 34 checks: 16 PASS, 3 WARNING, 0 FAIL, 13 N/A, 2 MANUAL REVIEW.

Findings by priority: P0 0, P1 2, P2 1, P3 2.

Scoring method: score = 100 * sum(weight * status_value) / sum(weight) over checks whose status is PASS (1.0), WARNING (0.5) or FAIL (0.0). N/A and MANUAL REVIEW are excluded from both numerator and denominator. The two scores use disjoint check sets. A score of null means no check in that set produced scorable evidence.

## P0 Blocking Issues

_An agent cannot access, discover or interpret essential content._

None identified.

## P1 High Impact

_Significant discoverability, machine-readability or entity-clarity problems._

- **Entity clarity** (WARNING, AEO): 1 entities lack a stable @id for cross-page linking
- **Structured data** (WARNING, AEO): 3 structured-data issues on the served homepage

## P2 Enhancements

_Improvements to efficiency or interoperability._

- **llms.txt** (WARNING, Availability): No llms.txt served. This is optional; absence is not a defect
  - Recommendation: Consider a curated llms.txt if the site has documentation or authoritative resources

## P3 Experimental

_Emerging standards and advanced capabilities. Never treated as blocking._

- **DNS-AID** (MANUAL REVIEW, Discoverability): DNS-AID requires a DNS record this toolkit never creates. Verify the current specification, then hand the record name, value and verification procedure to the DNS owner
  - Recommendation: Diagnostics only. See references/dns-aid.md for the reporting template
- **Web Bot Auth** (MANUAL REVIEW, Bot Access): No verified signature exchange observed. Web Bot Auth is a property of the requesting agent and the origin's verification policy; never fabricate cryptographic material

## Discoverability

| Check | Status | Score set | Evidence | Detail |
|---|---|---|---|---|
| robots.txt | PASS | Agent Readiness | local+live | Served robots.txt is valid and references 1 sitemap(s) |
| Sitemap | PASS | Agent Readiness | live | Sitemap valid, referenced from robots.txt, 4 URLs, sample all 2xx |
| HTTP Link headers | PASS | Agent Readiness | live | Link header advertises: sitemap |
| DNS-AID | MANUAL REVIEW | Agent Readiness | none | DNS-AID requires a DNS record this toolkit never creates. Verify the current specification, then hand the record name, value and verification procedure to the DNS owner |

## Content Accessibility

| Check | Status | Score set | Evidence | Detail |
|---|---|---|---|---|
| Markdown negotiation | PASS | Agent Readiness | live | Served text/markdown with Markdown structure |
| Server-rendered content | PASS | AEO Technical | local+live | Homepage delivers 3698 characters of text without JavaScript |
| Semantic HTML | PASS | AEO Technical | local+live | Served homepage uses landmarks and a coherent heading structure |

## Bot Access

| Check | Status | Score set | Evidence | Detail |
|---|---|---|---|---|
| AI Bot Rules | PASS | Agent Readiness | local+live | Served policy declares rules for: ChatGPT-User, Claude-User, ClaudeBot, GPTBot, Google-Extended, OAI-SearchBot, Perplexity-User, PerplexityBot |
| Actual bot access | PASS | Agent Readiness | live | Declared and actual access agree. Content served to: GPTBot, ClaudeBot, PerplexityBot, Googlebot, Bingbot |
| Content Signals | PASS | Agent Readiness | local+live | Content signals served: search=yes, ai-input=yes, ai-train=no |
| Web Bot Auth | MANUAL REVIEW | Agent Readiness | live | No verified signature exchange observed. Web Bot Auth is a property of the requesting agent and the origin's verification policy; never fabricate cryptographic material |

## Protocol Discovery

| Check | Status | Score set | Evidence | Detail |
|---|---|---|---|---|
| API Catalog | N/A | Agent Readiness | none | Not applicable: no API surface detected |
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
| x402 | N/A | Agent Readiness | none | Not applicable: No payment provider, cart, checkout or transaction code detected |
| MPP | N/A | Agent Readiness | none | Not applicable: No payment provider, cart, checkout or transaction code detected |
| UCP | N/A | Agent Readiness | none | Not applicable: No payment provider, cart, checkout or transaction code detected |
| ACP | N/A | Agent Readiness | none | Not applicable: No payment provider, cart, checkout or transaction code detected |

## AEO

| Check | Status | Score set | Evidence | Detail |
|---|---|---|---|---|
| Crawlability | PASS | AEO Technical | live | Homepage crawlable by general crawlers |
| Content availability | PASS | AEO Technical | local+live | Served homepage carries 607 words of extractable text |
| Entity clarity | WARNING | AEO Technical | local+live | 1 entities lack a stable @id for cross-page linking |
| Structured data | WARNING | AEO Technical | local+live | 3 structured-data issues on the served homepage |
| Answer extraction | PASS | AEO Technical | local+live | Homepage exposes a summary and a coherent heading outline |
| Citation readiness | PASS | AEO Technical | local+live | Homepage carries the signals needed to attribute it |
| Canonicalization | PASS | AEO Technical | local+live | Canonical declared: https://pulidotax.com/ |
| Content duplication | PASS | AEO Technical | local | No competing duplicate titles detected in the inspected documents |

## Availability

| Check | Status | Score set | Evidence | Detail |
|---|---|---|---|---|
| Homepage availability | PASS | Agent Readiness | live | HTTP 200 after 0 redirect(s) |
| llms.txt | WARNING | Agent Readiness | live | No llms.txt served. This is optional; absence is not a defect |

## Files Modified

None. This run is read-only: it inspects and reports, it does not edit the site.

## Tests Executed

- Local repository inspection (20 files scanned)
- Live origin inspection of https://pulidotax.com/

## Before / After

| Item | Before | After |
|---|---|---|
| Agent Readiness Score | 91/100 | 97/100 |
| AEO Technical Score | 90/100 | 90/100 |
| HTTP Link headers | WARNING | PASS |
| Markdown negotiation | WARNING | PASS |

## Remaining Manual Actions

- **DNS-AID**: DNS-AID requires a DNS record this toolkit never creates. Verify the current specification, then hand the record name, value and verification procedure to the DNS owner
- **Web Bot Auth**: No verified signature exchange observed. Web Bot Auth is a property of the requesting agent and the origin's verification policy; never fabricate cryptographic material

Owner decisions this toolkit will not make automatically: AI training and retrieval policy, DNS records, CDN/WAF rules, deployment, payment protocols, authentication, and any capability the site does not actually provide.

## Status Legend

| Status | Meaning |
|---|---|
| PASS | verified evidence |
| FAIL | applicable defect |
| WARNING | applicable but incomplete or unverified end to end |
| N/A | not applicable; excluded from scoring |
| MANUAL REVIEW | no evidence available here; needs owner, deployment, browser, DNS or specification verification |

