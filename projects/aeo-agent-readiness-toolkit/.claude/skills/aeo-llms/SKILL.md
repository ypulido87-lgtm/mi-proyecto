---
name: aeo-llms
description: Audit and optionally generate a curated llms.txt, or a justified llms-full.txt, as an agent-facing index of a site's most useful pages. Use for llms.txt questions, AI-readable content indexes, documentation discovery, or curated machine-readable site guidance.
---

# AEO llms.txt

`/llms.txt` is a curated index of the pages most useful to an agent. It is a
proposal, not a requirement.

**A missing llms.txt is never a critical failure.** Report it as an optional
enhancement (P2 at most). Do not create one for a site with little content to
index — an llms.txt listing four marketing pages helps nobody.

```bash
# Audit an existing file
python scripts/llms_txt.py audit ./public/llms.txt

# Propose a curated file from URLs that already exist
python scripts/llms_txt.py curate ./urls.txt --site-name "Example" --summary "What the site is" --output ./public/llms.txt
```

## Curation rules

It is an index, not a copy of the sitemap. Prioritise, in this order:

1. About and identity
2. Documentation and guides
3. API documentation
4. Products and services
5. Resources — blog, articles, case studies, FAQ, support
6. Policies — privacy, terms, security, accessibility
7. Contact

Exclude admin and login surfaces, account and dashboard pages, cart and checkout,
search results, tag and author archives, feeds, pagination, asset and data files,
URLs carrying query parameters or fragments, and anything temporary or staged.
The curator enforces these exclusions and reports each one with its reason.

## Honesty rules

- Only list URLs that exist in the project or that you verified on the live
  origin. Never invent a plausible-looking path.
- Verify each link resolves before publishing.
- Descriptions must match what the page actually contains.
- The file does not grant content-usage rights, and must not be presented as if
  it does. Content policy lives in
  [../aeo-bot-access/SKILL.md](../aeo-bot-access/SKILL.md).

## llms-full.txt

Only when there is a justified case — typically documentation-heavy sites where
full text in one file genuinely helps — and only when someone will keep it
current. A stale llms-full.txt is worse than none, because agents will read
outdated content as authoritative. If nobody owns its maintenance, do not create
it.

## Serving it

Place the file where the stack actually serves it, then confirm
`https://domain/llms.txt` returns HTTP 200 with `text/plain` or `text/markdown`.
A catch-all route returning HTML for `/llms.txt` is a `WARNING`, not a pass: the
file is not really there.

A starting template is in [assets/llms.txt.template](assets/llms.txt.template).
