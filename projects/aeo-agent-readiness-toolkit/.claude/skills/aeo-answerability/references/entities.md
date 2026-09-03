# Entity and structured-data checklist

Mark up only what the page actually shows or what is demonstrably true. Every
property below is a question about the page, not a field to fill in.

## Publisher identity — once per site, referenced everywhere

`Organization` (or `LocalBusiness`, or `Person` for a personal site)

Required: `name`, `url`. Strongly recommended: stable `@id`, `logo`, `sameAs`
pointing at real profiles, `description`. For `LocalBusiness` also `address`,
`telephone`, `openingHours` — and only if they appear on the site.

Give the publisher one `@id` (for example `https://example.com/#organization`)
and reference it from every page instead of repeating the object.

## Per-type essentials

| Type | Must have | Common mistakes |
|---|---|---|
| `Article` / `BlogPosting` / `NewsArticle` | `headline`, `datePublished`, `author`, `publisher` | `dateModified` in the future; author name not shown on the page |
| `Product` | `name`, `image`, `description` | `Offer` price or availability the page never displays |
| `Offer` | `price`, `priceCurrency`, `availability` | Currency omitted; price differs from the visible price |
| `Service` | `name`, `provider`, `areaServed` | Describing services the site does not offer |
| `Event` | `name`, `startDate`, `location` | Past events left marked as upcoming |
| `FAQPage` | `mainEntity` with real `Question`/`Answer` pairs | Questions nobody asks, written only to trigger a rich result |
| `BreadcrumbList` | Ordered `ListItem` with `position` | Breadcrumbs that do not match the real navigation |
| `Person` | `name` | `jobTitle` or credentials not evidenced anywhere |
| `WebSite` | `name`, `url` | `SearchAction` declared with no working site search |

## What makes markup fabricated

The auditor flags a structured `name` or `headline` that appears nowhere in the
visible text as a **P1 unsupported claim**. Also treat as fabricated:

- ratings or review counts with no visible reviews;
- prices or availability the page does not show;
- authors, dates or credentials that exist only in the markup;
- FAQ entries written for the markup rather than for readers;
- `sameAs` links to profiles that do not exist or belong to someone else.

This is not merely a policy preference: search and answer engines treat markup
that contradicts visible content as a quality violation, and it can cost the site
rich results entirely.

## Consistency

The same entity must be described the same way everywhere. Check organisation
name, URL and logo across pages, that `@id` values are stable and unique, and
that structured dates match visible dates.

## Verifying

`scripts/structured_data.py` checks JSON validity, plausibility and support in
visible text. It does **not** certify Schema.org semantics. Confirm with the
Google Rich Results Test and the Schema Markup Validator before claiming
correctness, and say in the report which tool confirmed what.
