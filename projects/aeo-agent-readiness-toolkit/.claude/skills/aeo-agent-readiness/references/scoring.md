# Scoring model

Two independent scores over **disjoint** check sets. They answer different
questions and are never averaged together.

## Formula

```
score = 100 * Σ(weight × status_value) / Σ(weight)

status_value:  PASS 1.0 | WARNING 0.5 | FAIL 0.0
excluded:      N/A, MANUAL REVIEW  (numerator and denominator both)
```

- `N/A` means the capability does not apply. It cannot lower a score, and it
  cannot raise one either.
- `MANUAL REVIEW` means no evidence was available — usually a live-only check run
  without a URL, or a specification that must be verified by a human. Scoring an
  unknown as a failure would punish local-only audits, so it is excluded.
- `WARNING` is partial credit: the capability exists but is incomplete or not
  verified end to end.
- A `null` score means nothing in that set produced scorable evidence. Report it
  as "not scored", never as `0`.

## Agent Readiness Score

Can an agent discover, reach, and interoperate with the site?

Discoverability (robots.txt, sitemap, `Link` headers, DNS-AID) · bot access
(declared rules, actual access, content signals, Web Bot Auth) · content
efficiency (Markdown negotiation, llms.txt) · protocol discovery (API catalog,
OAuth, Auth.md, MCP, A2A, Agent Skills, WebMCP, ARD) · commerce (x402, MPP, UCP,
ACP) · homepage availability.

## AEO Technical Score

Can an answer engine parse, understand and cite the content?

Crawlability · content availability · server-rendered content · semantic HTML ·
structured data · entity clarity · canonicalization · answer extraction ·
citation readiness · content duplication.

## Weights

Blocking access checks weigh more than experimental interoperability ones, so a
missing ARD manifest cannot outweigh a homepage that agents cannot read. Weights
live in `scripts/aeolib/scoring.py`; `CHECK_WEIGHTS` is the single source of
truth and defaults to 1.0 for anything unlisted.

Representative values:

| Check | Weight | Score set |
|---|---|---|
| Homepage availability | 3.0 | Agent Readiness |
| Actual bot access | 3.0 | Agent Readiness |
| robots.txt, Sitemap, AI Bot Rules | 2.0 | Agent Readiness |
| Server-rendered content | 3.0 | AEO Technical |
| Crawlability, Content availability | 3.0 | AEO Technical |
| Structured data | 2.5 | AEO Technical |
| DNS-AID, Web Bot Auth, WebMCP, ARD | 0.5 | Agent Readiness |

## Worked example

A brochure site with no API, no auth and no commerce:

```
Agent Readiness: applicable 6 | passed 4 | warnings 2 | failed 0 | N/A 9 | manual 6
AEO Technical:   applicable 10 | passed 6 | warnings 3 | failed 1 | N/A 0 | manual 0
```

The nine `N/A` results are correct outcomes, not gaps. Reporting them as failures
would push the owner toward publishing capabilities the site does not have.

## Relationship to isitagentready.com

The Agent Readiness Score follows the same journey — discover, access, parse,
understand, cite, interact, transact — but it is computed independently and is
not a prediction of that site's score. The objective is a site agents can really
use, not a number.
