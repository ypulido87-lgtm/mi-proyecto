# AEO & Agent Readiness Audit

Domain: Not provided
Project: AEO Agent Readiness Toolkit
Stack: Unknown
Site Type: Unknown
Date: 2026-08-24T13:50:53+00:00
Evidence layers: local only

Agent Readiness Score: not scored (no applicable evidence)  
  applicable 0 | passed 0 | warnings 0 | failed 0 | N/A 13 | manual review 11

AEO Technical Score: not scored (no applicable evidence)  
  applicable 0 | passed 0 | warnings 0 | failed 0 | N/A 9 | manual review 1

## Executive Summary

The audit ran 34 checks: 0 PASS, 0 WARNING, 0 FAIL, 22 N/A, 12 MANUAL REVIEW.

Findings by priority: P0 0, P1 1, P2 11, P3 0.

No public URL was supplied, so every live check is MANUAL REVIEW rather than a defect. A file in the repository is not proof that it is served: re-run with `--url` to confirm.

Scoring method: score = 100 * sum(weight * status_value) / sum(weight) over checks whose status is PASS (1.0), WARNING (0.5) or FAIL (0.0). N/A and MANUAL REVIEW are excluded from both numerator and denominator. The two scores use disjoint check sets. A score of null means no check in that set produced scorable evidence.

## P0 Blocking Issues

_An agent cannot access, discover or interpret essential content._

None identified.

## P1 High Impact

_Significant discoverability, machine-readability or entity-clarity problems._

- **Actual bot access** (MANUAL REVIEW, Bot Access): Requires a live origin: edge and origin behaviour can only be observed against a live origin

## P2 Enhancements

_Improvements to efficiency or interoperability._

- **AI Bot Rules** (MANUAL REVIEW, Bot Access): No web content detected in this project. If it is deployed, re-run with --url.
- **Content Signals** (MANUAL REVIEW, Bot Access): No web content detected in this project. If it is deployed, re-run with --url.
- **Crawlability** (MANUAL REVIEW, AEO): No web content detected in this project. If it is deployed, re-run with --url.
- **DNS-AID** (MANUAL REVIEW, Discoverability): Requires a live origin: DNS records are external to the repository and are never modified by this toolkit
- **HTTP Link headers** (MANUAL REVIEW, Discoverability): Requires a live origin: response headers require a live origin
- **Homepage availability** (MANUAL REVIEW, Availability): Requires a live origin: no public URL supplied
- **Markdown negotiation** (MANUAL REVIEW, Content Accessibility): Requires a live origin: content negotiation requires a live origin or a running server
- **Sitemap** (MANUAL REVIEW, Discoverability): No web content detected in this project. If it is deployed, re-run with --url.
- **Web Bot Auth** (MANUAL REVIEW, Bot Access): Requires a live origin: signature verification requires live request/response exchange
- **llms.txt** (MANUAL REVIEW, Availability): No web content detected in this project. If it is deployed, re-run with --url.
- **robots.txt** (MANUAL REVIEW, Discoverability): No web content detected in this project. If it is deployed, re-run with --url.

## P3 Experimental

_Emerging standards and advanced capabilities. Never treated as blocking._

None identified.

## Discoverability

| Check | Status | Score set | Evidence | Detail |
|---|---|---|---|---|
| robots.txt | MANUAL REVIEW | Agent Readiness | none | No web content detected in this project. If it is deployed, re-run with --url. |
| Sitemap | MANUAL REVIEW | Agent Readiness | none | No web content detected in this project. If it is deployed, re-run with --url. |
| HTTP Link headers | MANUAL REVIEW | Agent Readiness | none | Requires a live origin: response headers require a live origin |
| DNS-AID | MANUAL REVIEW | Agent Readiness | none | Requires a live origin: DNS records are external to the repository and are never modified by this toolkit |

## Content Accessibility

| Check | Status | Score set | Evidence | Detail |
|---|---|---|---|---|
| Markdown negotiation | MANUAL REVIEW | Agent Readiness | none | Requires a live origin: content negotiation requires a live origin or a running server |
| Server-rendered content | N/A | AEO Technical | none | Not applicable: no HTML content in this project |
| Semantic HTML | N/A | AEO Technical | none | Not applicable: no HTML content in this project |

## Bot Access

| Check | Status | Score set | Evidence | Detail |
|---|---|---|---|---|
| AI Bot Rules | MANUAL REVIEW | Agent Readiness | none | No web content detected in this project. If it is deployed, re-run with --url. |
| Actual bot access | MANUAL REVIEW | Agent Readiness | none | Requires a live origin: edge and origin behaviour can only be observed against a live origin |
| Content Signals | MANUAL REVIEW | Agent Readiness | none | No web content detected in this project. If it is deployed, re-run with --url. |
| Web Bot Auth | MANUAL REVIEW | Agent Readiness | none | Requires a live origin: signature verification requires live request/response exchange |

## Protocol Discovery

| Check | Status | Score set | Evidence | Detail |
|---|---|---|---|---|
| API Catalog | N/A | Agent Readiness | none | Not applicable: no API surface detected in this project |
| OAuth discovery | N/A | Agent Readiness | none | Not applicable: no OAuth implementation detected; publishing discovery metadata would be a false signal |
| OAuth Protected Resource | N/A | Agent Readiness | none | Not applicable: no OAuth implementation detected; publishing discovery metadata would be a false signal |
| Auth.md | N/A | Agent Readiness | none | Not applicable: no authentication surface detected |
| MCP Server Card | N/A | Agent Readiness | none | Not applicable: this project does not implement an MCP server |
| A2A Agent Card | N/A | Agent Readiness | none | Not applicable: this project does not expose an agent service |
| Agent Skills | N/A | Agent Readiness | none | Not applicable: no agent-executable capabilities are offered by this site |
| WebMCP | N/A | Agent Readiness | none | Not applicable: no in-page agent tools are implemented |
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
| Crawlability | MANUAL REVIEW | AEO Technical | none | No web content detected in this project. If it is deployed, re-run with --url. |
| Content availability | N/A | AEO Technical | none | Not applicable: no HTML content in this project |
| Entity clarity | N/A | AEO Technical | none | Not applicable: no HTML content in this project |
| Structured data | N/A | AEO Technical | none | Not applicable: no HTML content in this project |
| Answer extraction | N/A | AEO Technical | none | Not applicable: no HTML content in this project |
| Citation readiness | N/A | AEO Technical | none | Not applicable: no HTML content in this project |
| Canonicalization | N/A | AEO Technical | none | Not applicable: no HTML content in this project |
| Content duplication | N/A | AEO Technical | none | Not applicable: no HTML content in this project |

## Availability

| Check | Status | Score set | Evidence | Detail |
|---|---|---|---|---|
| Homepage availability | MANUAL REVIEW | Agent Readiness | none | Requires a live origin: no public URL supplied |
| llms.txt | MANUAL REVIEW | Agent Readiness | none | No web content detected in this project. If it is deployed, re-run with --url. |

## Files Modified

None. This run is read-only: it inspects and reports, it does not edit the site.

## Tests Executed

- Local repository inspection (6 files scanned)

## Before / After

| Item | Before | After |
|---|---|---|
| Agent Readiness Score | not scored | not scored |
| AEO Technical Score | not scored | not scored |
| Check statuses | no change | no change |

## Remaining Manual Actions

- **robots.txt**: No web content detected in this project. If it is deployed, re-run with --url.
- **Sitemap**: No web content detected in this project. If it is deployed, re-run with --url.
- **HTTP Link headers**: Requires a live origin: response headers require a live origin
- **DNS-AID**: Requires a live origin: DNS records are external to the repository and are never modified by this toolkit
- **Markdown negotiation**: Requires a live origin: content negotiation requires a live origin or a running server
- **AI Bot Rules**: No web content detected in this project. If it is deployed, re-run with --url.
- **Actual bot access**: Requires a live origin: edge and origin behaviour can only be observed against a live origin
- **Content Signals**: No web content detected in this project. If it is deployed, re-run with --url.
- **Web Bot Auth**: Requires a live origin: signature verification requires live request/response exchange
- **Crawlability**: No web content detected in this project. If it is deployed, re-run with --url.
- **Homepage availability**: Requires a live origin: no public URL supplied
- **llms.txt**: No web content detected in this project. If it is deployed, re-run with --url.

Owner decisions this toolkit will not make automatically: AI training and retrieval policy, DNS records, CDN/WAF rules, deployment, payment protocols, authentication, and any capability the site does not actually provide.

## Status Legend

| Status | Meaning |
|---|---|
| PASS | verified evidence |
| FAIL | applicable defect |
| WARNING | applicable but incomplete or unverified end to end |
| N/A | not applicable; excluded from scoring |
| MANUAL REVIEW | no evidence available here; needs owner, deployment, browser, DNS or specification verification |

