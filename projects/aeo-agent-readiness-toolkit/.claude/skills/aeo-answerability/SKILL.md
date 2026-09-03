---
name: aeo-answerability
description: Audit whether pages can be understood and cited by answer engines, covering entity clarity, JSON-LD structured data, answer extraction, citation readiness, canonicalization and competing duplicate content. Use for Answer Engine Optimization, Schema.org review, entity identity, FAQs, author and date attribution, or factual answer extraction.
---

# AEO Answerability

This module is AEO beyond agent readiness: can a page be correctly understood and
used as a source for an answer?

```bash
python scripts/structured_data.py https://example.com
python scripts/structured_data.py ./dist/about.html
```

## Entity clarity

Identify who or what the page is about: `Organization`, `Person`, `Product`,
`Service`, `Brand`, `Place`, `Event`, `Article`, `FAQPage`, `BreadcrumbList`.

Check that:

- a publisher entity exists (`Organization`, `LocalBusiness` or `Person`);
- entities carry a stable `@id` so they can be linked across pages;
- relationships are explicit — author to publisher, product to offer, article to
  its subject;
- `sameAs` points at real, authoritative profiles;
- the same entity is not described inconsistently across pages.

## Structured data

The auditor separates three distinct questions, because conflating them is the
most common structured-data mistake:

1. **Does the JSON parse?** A syntax error is a `FAIL`.
2. **Is it plausible Schema.org?** Missing recommended properties, a non
   `schema.org` `@context`, unknown types, duplicate `@id` values, malformed URLs.
3. **Is it true?** A structured `name` or `headline` that appears nowhere in the
   visible text is flagged **P1 as an unsupported claim**.

Valid JSON is never proof of correct Schema.org, and the report says so
explicitly. Use the Rich Results Test or the Schema Markup Validator for semantic
confirmation before claiming correctness.

**Never generate structured data for content the page does not show.** Markup
must describe information that is visible or demonstrably valid: no invented
ratings, prices, authors, dates, FAQs or credentials.

## Answer extraction

For each important page check that it has a descriptive title, a direct answer
near the top, semantic subheadings, clear definitions, verifiable facts, tables
where they help, genuine FAQs, sources, dates, an author, a modified date, a
canonical URL and entity context.

Flag: no meta description, skipped or empty headings, almost no heading
structure, and thin content (under ~150 words of served text).

FAQ markup must reflect questions a user genuinely asks and answers the page
genuinely gives. Invented FAQ blocks written to trigger a rich result are exactly
the false signal this toolkit refuses to create.

## Citation readiness

An answer engine cites what it can attribute. Check that a factual claim can be
tied to a page, an entity, a date, an author, a source and a canonical URL.
`citation_readiness.ready` requires canonical, title and a date together.

## Canonicalization

Every page should declare exactly one canonical URL, on the same host, consistent
with the served URL after redirects. A cross-host canonical or a missing canonical
on every page is a `FAIL`.

## Content duplication

Detect pages competing for the same answer or entity — shared titles are the
first signal. Report them with a recommendation to differentiate or consolidate.

**Never rewrite, merge or delete content automatically.** Content decisions belong
to the owner; produce recommendations and let them choose.

See [references/entities.md](references/entities.md) for the entity checklist and
the properties that matter per type.
