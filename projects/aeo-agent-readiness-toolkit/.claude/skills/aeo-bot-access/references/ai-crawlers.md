# AI crawlers and content signals

Reference for the tokens this module probes. Inclusion here is **not** a
recommendation to allow or block anything.

## Why the purpose matters

The three purposes below have different consequences, and collapsing them into
one "block AI" decision is the most common mistake owners make.

| Purpose | What blocking it means |
|---|---|
| Training | The content is not used to train models. Visibility in assistants is largely unaffected. |
| Search / retrieval | The site stops appearing in that assistant's answers and citations. This is a visibility decision, not a copyright one. |
| User-triggered | A person's own agent cannot fetch a page they explicitly asked about. |

Present all three separately and let the owner decide each one.

## Documented tokens

| Token | Operator | Published purpose |
|---|---|---|
| GPTBot | OpenAI | Training |
| OAI-SearchBot | OpenAI | Search indexing |
| ChatGPT-User | OpenAI | User-triggered fetch |
| ClaudeBot | Anthropic | Training |
| Claude-SearchBot | Anthropic | Search indexing |
| Claude-User | Anthropic | User-triggered fetch |
| Google-Extended | Google | Generative AI training control |
| Googlebot | Google | Search indexing |
| Applebot-Extended | Apple | Training control |
| Applebot | Apple | Search indexing |
| PerplexityBot | Perplexity | Search indexing |
| Perplexity-User | Perplexity | User-triggered fetch |
| CCBot | Common Crawl | Open crawl corpus |
| Meta-ExternalAgent | Meta | Training |
| Bytespider | ByteDance | Training |
| Amazonbot | Amazon | Search indexing |
| Bingbot | Microsoft | Search indexing |

Operators change tokens and purposes. Verify against the operator's own
documentation before advising, and record the date checked.

## Content signals

`Content-Signal` declares intent for `search`, `ai-input` and `ai-train`. It is
emerging: verify the current syntax before writing one.

It expresses a preference. It is not technical enforcement and it is not a
licence. Never describe it to an owner as either.

## Declared versus actual

robots.txt is voluntary. What actually reaches an agent is decided by the origin,
the CDN and the WAF. Always test both, and report:

- **declared** — what robots.txt and meta robots say;
- **actual** — the status code, challenge or content a real request receives.

A site whose robots.txt welcomes ClaudeBot while Cloudflare returns 403 to it is
not welcoming ClaudeBot. That gap is the finding.
