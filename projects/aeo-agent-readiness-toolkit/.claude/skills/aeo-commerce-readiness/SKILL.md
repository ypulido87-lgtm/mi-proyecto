---
name: aeo-commerce-readiness
description: Audit agent commerce readiness for x402, MPP, UCP and ACP, but only when a site genuinely has products, carts, checkout, bookings, subscriptions, payment APIs or a payment provider. Use when checking agentic commerce, checkout interoperability, payment protocol applicability, or whether commerce checks apply at all.
---

# AEO Commerce Readiness

Most sites are not commerce sites. Detect real transaction capability **first**;
if there is none, every protocol here is `N/A` and the audit moves on.

## Detect before assessing

```bash
python scripts/commerce_protocols.py --origin https://example.com
```

Evidence that makes commerce applicable:

- a payment dependency (Stripe, Braintree, PayPal, Adyen, Mollie, Square,
  Razorpay, Snipcart, Shopify, Medusa, Saleor, WooCommerce, Paddle, and similar);
- transaction code — cart mutations, checkout sessions, payment intents, order or
  line-item handling;
- a real checkout, cart, booking or subscription flow.

Evidence that does **not** make it applicable: a `/pricing` page, the word
"products" in a directory name, a contact form, or a marketing page describing
paid services. Directory names alone are explicitly rejected by the detector; a
brochure site that mentions prices is not a transaction surface.

When commerce is absent, mark x402, MPP, UCP and ACP as `N/A — no commerce or
payment capability detected` and record why. This is not a failure and must not
reduce the score.

## When commerce does exist

| Protocol | Purpose |
|---|---|
| x402 | HTTP-native payments built on the 402 Payment Required status |
| MPP | Machine payable protocol for agent-initiated purchases |
| UCP | Universal commerce protocol for catalogue and checkout interoperability |
| ACP | Agentic commerce protocol for delegated purchase flows |

All four are emerging or pre-1.0. The toolkit reports them as `MANUAL REVIEW` and
provides **no implementation**. Verify the current official specification before
recommending anything, and record the source and date in the report.

## Hard limits

- Never implement a payment protocol to improve a score.
- Never publish a commerce capability declaration that the site cannot honour — an
  agent acting on it would attempt a real transaction and fail.
- Never create, modify or expose payment credentials, keys or webhooks.
- Never alter checkout, pricing or order logic as part of an AEO audit.

Structured commerce data is a different matter and belongs to
[../aeo-answerability/SKILL.md](../aeo-answerability/SKILL.md): `Product`,
`Offer` and `AggregateRating` markup describing genuinely visible products is
legitimate and useful. Markup that describes products, prices or availability the
page does not show is fabricated and must be reported as a defect.

See [references/commerce-protocols.md](references/commerce-protocols.md) for what
is known, what is unverified, and what must never be assumed.
