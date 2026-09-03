---
name: aeo-discoverability
description: Audit and improve website discoverability for AI agents, covering robots.txt syntax and precedence, sitemaps, HTTP Link headers, real public responses and DNS-AID diagnostics. Use when checking AI crawler visibility, robots or sitemap problems, machine-readable discovery, or isitagentready discoverability failures.
---

# AEO Discoverability

Can an agent find the site's content at all? Audit robots.txt, sitemaps, `Link`
headers and DNS-based discovery — across both the repository and the live origin.

**A file in the repository is not a published file.** Always confirm the served
response before calling a discovery check `PASS`.

## robots.txt

```bash
python scripts/robots_parser.py https://example.com/robots.txt
python scripts/robots_parser.py ./public/robots.txt --user-agent GPTBot --path /blog
```

The parser implements RFC 9309 grouping and longest-match precedence, so it
reports what a compliant crawler will actually do, not what a regex guesses.

Verify:

- the file is served with HTTP 200 and a text content type — HTML returned from a
  catch-all route is a `FAIL`, not a pass;
- syntax errors and directives that appear before any `User-agent` group;
- `Allow`/`Disallow` conflicts on the same path;
- at least one `Sitemap:` reference (these are global directives, not group members);
- which documented AI crawlers have explicit rules, and what those rules do.

Report the current AI-crawler policy explicitly and never change it on your own.
Allowing or blocking GPTBot, ClaudeBot, CCBot, Google-Extended, PerplexityBot and
the rest is the owner's decision. Show the current policy and any proposed diff,
then wait for approval.

A `Disallow: /` for the wildcard group is P0. A missing robots.txt is not: RFC
9309 treats an unavailable robots.txt as unrestricted crawling.

## Sitemap

```bash
python scripts/sitemap_validator.py https://example.com/sitemap.xml --origin https://example.com --check-urls 25
```

Verify XML well-formedness, the sitemaps.org 0.9 namespace, absolute same-origin
URLs, absence of query strings and fragments, duplicates, the 50,000 entry and
50 MiB limits, `lastmod` in W3C date format, and that a sample of URLs really
returns 2xx without redirecting. Sitemap indexes are followed one level.

Cross-check: URLs listed in the sitemap must not be disallowed in robots.txt, and
the sitemap must be referenced from robots.txt. Private, staged, paginated and
parameterised URLs do not belong there.

## HTTP Link headers

```bash
python scripts/http_inspect.py https://example.com
```

Inspect the real headers, the full redirect chain, `Link` (RFC 8288), canonical,
`X-Robots-Tag`, `Vary` and cache directives. Only propose a `Link` relation when
the target resource exists and the relation is registered and justified. An
advertised relation pointing at a missing resource is a false signal.

## DNS-AID

Diagnostics only. DNS lives outside the repository and this toolkit never edits
it. Produce the reporting template in
[references/dns-aid.md](references/dns-aid.md): diagnosis, required record name,
proposed value, who owns the zone, implementation instructions and a verification
procedure. Verify the current specification before proposing any value; if it
cannot be verified, report `MANUAL REVIEW`.

## Fixing

Safe, in-scope fixes: adding a missing `Sitemap:` reference, correcting a syntax
error, generating a sitemap from canonical URLs that already exist, removing a
stale disallow that the owner confirms is obsolete.

Out of scope without explicit instruction: changing crawler permissions, adding
or removing AI-crawler rules, editing DNS, touching CDN or WAF configuration.

Place generated files where the stack actually serves them — `public/`, `static/`,
web root, or the framework's route/middleware — then re-fetch the public URL to
confirm. An asset template is in [assets/robots.txt.template](assets/robots.txt.template).
