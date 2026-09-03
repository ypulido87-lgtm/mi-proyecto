---
name: aeo-content-accessibility
description: Audit and improve how efficiently agents can read a site, covering Markdown content negotiation, server-rendered content, JavaScript-only content risk, semantic HTML, headings, links, forms, tables and lists. Use when checking AEO content extraction, markdown responses, JS-rendered pages, or semantic HTML quality.
---

# AEO Content Accessibility

Once an agent can reach a page, can it read it efficiently? This module covers
what the server actually sends — not what a browser eventually renders.

## Server-rendered content

The single highest-impact check here. Most crawlers and answer engines do not
execute JavaScript.

```bash
python scripts/semantic_html.py https://example.com
python scripts/semantic_html.py ./dist/index.html
```

`javascript_dependent_content: true` means the served HTML carries almost no text
and depends on executable script — an empty page for a non-executing agent. That
is **P0**.

The analyser deliberately does not count `<script type="application/ld+json">` or
other data blocks as a JavaScript dependency, and does not flag a short page that
has real headings and text.

Remedies, in order of preference: server-side rendering, static generation,
pre-rendering for bots, or at minimum a meaningful `<noscript>` equivalent. For
Next.js/Nuxt/Astro/SvelteKit this is usually a rendering-mode change, not a
rewrite. Never restructure an application's rendering strategy without approval —
report it and propose the change.

## Semantic HTML

Review landmarks (`main`, `article`, `section`, `nav`, `header`, `footer`),
heading hierarchy, real `<a href>` links, buttons with accessible names, labelled
inputs, tables with `<th>`, and lists.

Findings the analyser produces:

- no `h1`, or several competing `h1` elements;
- skipped heading levels and empty headings;
- images without `alt`, inputs without a label, buttons with no accessible name;
- links whose only text is "click here" or "read more";
- a low text-to-markup ratio.

Fix the markup, not the design. Do not change visual layout unless a fix strictly
requires it, and say so when it does.

## Markdown content negotiation

```bash
python scripts/markdown_negotiation.py https://example.com
```

The tester requests the same URL with `Accept: text/html` and
`Accept: text/markdown`, then compares status, content type, structural evidence
and byte size.

`PASS` requires a Markdown content type **and** Markdown structure. HTML returned
with a 200 is a `WARNING`, never a pass — a body that merely contains a line
starting with `#` is not Markdown. Identical bodies for both headers means no
negotiation is happening.

This is an optional efficiency feature (typically a large byte reduction), not a
defect when absent. Implement it only when the stack supports negotiation
cleanly, HTML stays the default representation, and `Vary: Accept` is set so
caches do not serve the wrong representation. Never break the HTML response to
add it.

## Without a live origin

Content negotiation and rendered output cannot be judged from source alone. Mark
those `MANUAL REVIEW` and request the public URL, rather than guessing from
templates. Local template files are still worth inspecting for landmark and
heading structure — say clearly which layer produced each conclusion.
