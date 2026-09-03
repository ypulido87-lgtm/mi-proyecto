# Markdown content negotiation

Serving `text/markdown` to agents that ask for it typically cuts payload size
substantially and removes navigation, scripts and styling noise from what the
agent has to parse.

It is an **optional efficiency feature**. Absence is a `WARNING` at P2, never a
defect.

## What PASS requires

Both of these, together:

1. `Content-Type: text/markdown` (or `text/x-markdown`) on the response to
   `Accept: text/markdown`;
2. a body with real Markdown structure.

HTML returned with HTTP 200 is a `WARNING`. A body that merely contains a line
starting with a hash proves nothing, because HTML pages contain such lines inside
preformatted blocks, inline scripts and CSS. The tester judges by structure and
HTML tag density, and compares the two bodies to detect a server that ignores
`Accept` entirely.

## Correctness requirements

- **HTML stays the default.** A request without `Accept: text/markdown`, or with
  a wildcard Accept header, must still receive HTML. Browsers must be unaffected.
- **`Vary: Accept` is mandatory.** Without it, a CDN or browser cache will serve
  the Markdown representation to a browser, or the HTML to an agent. This is the
  most common way a well-intentioned implementation breaks a site.
- **Same URL, same content.** The Markdown must faithfully represent the same
  page: same headings, same links, same substance. Silently dropping content is
  worse than not offering Markdown at all.
- Preserve headings, link targets, lists and tables. Drop navigation chrome,
  scripts and styling.

## Implementation notes by stack

| Stack | Where negotiation belongs |
|---|---|
| Next.js | Middleware or a route handler inspecting the Accept header |
| Nuxt / Nitro | Server middleware |
| Astro / SvelteKit | Server endpoint or hook |
| Express / Fastify / Hono | Content-negotiation middleware |
| Django / Flask / FastAPI | Response rendering keyed on the Accept header |
| Laravel / Symfony | Middleware or a response listener |
| WordPress / Joomla | Plugin or template-level handling; verify caching plugins honour Vary |
| Static hosting | Edge function (Cloudflare Workers, Netlify, Vercel) or a pre-built .md file alongside each page |

For content that already exists as Markdown, which covers most static site
generators and documentation sites, serving the source is usually the least risky
approach.

## Verifying

```bash
python ../scripts/markdown_negotiation.py https://example.com
```

Afterwards confirm that the ordinary HTML response is unchanged, that
`Vary: Accept` is present, and that a cached second request still returns the
correct representation for each Accept header.
