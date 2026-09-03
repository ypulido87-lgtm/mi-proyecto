---
name: aeo-bot-access
description: Audit AI bot access by comparing declared robots policy with the access bots actually receive, covering CDN or WAF contradictions, HTTP status, meta robots, content signals and Web Bot Auth applicability. Use when checking AI crawler access, declared versus actual access, bot blocking, or content training and retrieval policy.
---

# AEO Bot Access

robots.txt states intent. A CDN, WAF, origin rule or rate limiter states reality.
This module finds where the two disagree.

## Declared vs actual access

```bash
python scripts/bot_access.py https://example.com
```

The prober requests the same URL as a browser and as several documented crawlers,
then classifies each result:

| Verdict | Meaning |
|---|---|
| `CONSISTENT_ALLOW` | Allowed by robots and actually served |
| `CONSISTENT_BLOCK` | Disallowed by robots and not served |
| `CONTRADICTION` | robots allows it, but the origin or edge returns an error or a challenge |
| `DECLARED_BLOCK_NOT_ENFORCED` | robots disallows it, yet content is served — robots is voluntary, not enforcement |

A `CONTRADICTION` is **P0**: the owner believes those agents are welcome and they
are being turned away. Typical causes are Cloudflare bot-fight rules, WAF managed
rules, a rate limiter, or a hosting provider's bot filter.

Report edge findings as external evidence. **Never modify CDN, WAF or firewall
configuration** — describe the contradiction, name the likely control, and hand
it to whoever owns that infrastructure.

Also correlate `X-Robots-Tag`, `<meta name="robots">` and HTTP status. A page
that is crawlable but carries `noindex` is a different failure from a blocked
page, and both matter.

## Content signals

Detect the declared policy for `search`, `ai-input` and `ai-train` and report it
verbatim.

If no policy exists, that is a finding, not a licence to invent one. Present the
technically valid options and the consequences of each, then let the owner
choose. **Never set, change or remove a content-usage policy without an explicit
instruction from the owner** — these are legal statements about their content,
not a score to optimise.

The same applies to per-crawler rules: the toolkit shows the current policy and a
proposed diff, and waits.

## Web Bot Auth

A compatibility check only. Whether an origin verifies signed bot requests is a
property of the origin's verification policy and the requesting agent's keys.

Report whether signature headers are observed and whether the stack could support
verification. **Never fabricate cryptographic material, keys, signatures or a
verification claim.** If applicability cannot be established, report
`MANUAL REVIEW`.

See [references/ai-crawlers.md](references/ai-crawlers.md) for the crawler tokens
this module probes and the purpose each operator publishes.
