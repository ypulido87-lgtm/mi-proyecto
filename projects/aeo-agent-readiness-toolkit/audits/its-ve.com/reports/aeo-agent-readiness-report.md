# AEO & Agent Readiness Audit

Domain: https://its-ve.com/
Project: its-ve.com
Stack: Unknown
Site Type: Unknown
Date: 2026-08-24T15:36:42+00:00
Evidence layers: local+live

> **TLS certificate verification was disabled for this run.** Live results are diagnostics only.

Agent Readiness Score: 81/100  
  applicable 9 | passed 4 | warnings 5 | failed 0 | N/A 13 | manual review 2

AEO Technical Score: 80/100  
  applicable 9 | passed 5 | warnings 4 | failed 0 | N/A 0 | manual review 1

## Executive Summary

The audit ran 34 checks: 9 PASS, 9 WARNING, 0 FAIL, 13 N/A, 3 MANUAL REVIEW.

Findings by priority: P0 0, P1 4, P2 6, P3 2.

Scoring method: score = 100 * sum(weight * status_value) / sum(weight) over checks whose status is PASS (1.0), WARNING (0.5) or FAIL (0.0). N/A and MANUAL REVIEW are excluded from both numerator and denominator. The two scores use disjoint check sets. A score of null means no check in that set produced scorable evidence.

## P0 Blocking Issues

_An agent cannot access, discover or interpret essential content._

None identified.

## P1 High Impact

_Significant discoverability, machine-readability or entity-clarity problems._

- **Answer extraction** (WARNING, AEO): Homepage answer extraction weakened by: heading levels skip
- **Entity clarity** (WARNING, AEO): Multiple Organization entities are declared and 2 entities carry no @id, so the publishing entity is ambiguous
- **Semantic HTML** (WARNING, Content Accessibility): 3 semantic issues in the served homepage
- **Structured data** (WARNING, AEO): 1 structured-data issues on the served homepage

## P2 Enhancements

_Improvements to efficiency or interoperability._

- **AI Bot Rules** (WARNING, Bot Access): No AI-crawler-specific rules are served; the wildcard group applies
- **Content Signals** (WARNING, Bot Access): No content-usage policy is served. Absence is reported, never assumed
- **Content duplication** (MANUAL REVIEW, AEO): No local source supplied; judged from the live origin only
- **HTTP Link headers** (WARNING, Discoverability): No Link header. Only add relations that point at resources which actually exist
- **Markdown negotiation** (WARNING, Content Accessibility): Identical body for both Accept headers; no negotiation
  - Recommendation: Optional efficiency feature. Implement only if the stack supports negotiation without breaking HTML
- **llms.txt** (WARNING, Availability): No llms.txt served. This is optional; absence is not a defect

## P3 Experimental

_Emerging standards and advanced capabilities. Never treated as blocking._

- **DNS-AID** (MANUAL REVIEW, Discoverability): DNS-AID requires a DNS record this toolkit never creates. Verify the current specification, then hand the record name, value and verification procedure to the DNS owner
  - Recommendation: Diagnostics only. See references/dns-aid.md for the reporting template
- **Web Bot Auth** (MANUAL REVIEW, Bot Access): No verified signature exchange observed. Web Bot Auth is a property of the requesting agent and the origin's verification policy; never fabricate cryptographic material

## Discoverability

| Check | Status | Score set | Evidence | Detail |
|---|---|---|---|---|
| robots.txt | PASS | Agent Readiness | live | Served robots.txt is valid and references 1 sitemap(s) |
| Sitemap | PASS | Agent Readiness | live | Sitemap valid, referenced from robots.txt, 33 URLs, sample all 2xx |
| HTTP Link headers | WARNING | Agent Readiness | live | No Link header. Only add relations that point at resources which actually exist |
| DNS-AID | MANUAL REVIEW | Agent Readiness | none | DNS-AID requires a DNS record this toolkit never creates. Verify the current specification, then hand the record name, value and verification procedure to the DNS owner |

## Content Accessibility

| Check | Status | Score set | Evidence | Detail |
|---|---|---|---|---|
| Markdown negotiation | WARNING | Agent Readiness | live | Identical body for both Accept headers; no negotiation |
| Server-rendered content | PASS | AEO Technical | live | Homepage delivers 3604 characters of text without JavaScript |
| Semantic HTML | WARNING | AEO Technical | live | 3 semantic issues in the served homepage |

## Bot Access

| Check | Status | Score set | Evidence | Detail |
|---|---|---|---|---|
| AI Bot Rules | WARNING | Agent Readiness | live | No AI-crawler-specific rules are served; the wildcard group applies |
| Actual bot access | PASS | Agent Readiness | live | Declared and actual access agree. Content served to: GPTBot, ClaudeBot, PerplexityBot, Googlebot, Bingbot |
| Content Signals | WARNING | Agent Readiness | live | No content-usage policy is served. Absence is reported, never assumed |
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
| x402 | N/A | Agent Readiness | none | Not applicable: no local source supplied and no commerce capability observed live |
| MPP | N/A | Agent Readiness | none | Not applicable: no local source supplied and no commerce capability observed live |
| UCP | N/A | Agent Readiness | none | Not applicable: no local source supplied and no commerce capability observed live |
| ACP | N/A | Agent Readiness | none | Not applicable: no local source supplied and no commerce capability observed live |

## AEO

| Check | Status | Score set | Evidence | Detail |
|---|---|---|---|---|
| Crawlability | PASS | AEO Technical | live | Homepage crawlable by general crawlers |
| Content availability | PASS | AEO Technical | live | Served homepage carries 505 words of extractable text |
| Entity clarity | WARNING | AEO Technical | live | Multiple Organization entities are declared and 2 entities carry no @id, so the publishing entity is ambiguous |
| Structured data | WARNING | AEO Technical | live | 1 structured-data issues on the served homepage |
| Answer extraction | WARNING | AEO Technical | live | Homepage answer extraction weakened by: heading levels skip |
| Citation readiness | PASS | AEO Technical | live | Homepage carries the signals needed to attribute it |
| Canonicalization | PASS | AEO Technical | live | Canonical declared: https://its-ve.com/ |
| Content duplication | MANUAL REVIEW | AEO Technical | none | No local source supplied; judged from the live origin only |

## Availability

| Check | Status | Score set | Evidence | Detail |
|---|---|---|---|---|
| Homepage availability | PASS | Agent Readiness | live | HTTP 200 after 0 redirect(s) |
| llms.txt | WARNING | Agent Readiness | live | No llms.txt served. This is optional; absence is not a defect |

## Files Modified

None. This run is read-only: it inspects and reports, it does not edit the site.

## Tests Executed

- Local repository inspection (2 files scanned)
- Live origin inspection of https://its-ve.com/ (TLS verification DISABLED)

## Before / After

| Item | Before | After |
|---|---|---|
| Agent Readiness Score | 81/100 | 81/100 |
| AEO Technical Score | 80/100 | 80/100 |
| Check statuses | no change | no change |

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

