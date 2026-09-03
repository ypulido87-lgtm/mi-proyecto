# Agent commerce protocols

All four protocols below are emerging or pre-1.0. This file records what the
toolkit treats as known, unknown, and forbidden to assume.

## Status

| Protocol | What it addresses | Toolkit stance |
|---|---|---|
| x402 | HTTP-native payment using the 402 Payment Required status | Detect a real 402 challenge; never generate one |
| MPP | Machine payable protocol for agent-initiated purchases | Report only; verify the specification first |
| UCP | Universal commerce protocol for catalogue and checkout interoperability | Report only; verify the specification first |
| ACP | Agentic commerce protocol for delegated purchase flows | Report only; verify the specification first |

The toolkit provides **no implementation** for any of them. Each is reported as
`MANUAL REVIEW` when commerce exists, and `N/A` when it does not.

## Why implementation is withheld

A commerce protocol declaration is a promise that an agent can complete a
transaction. If the promise is wrong, an agent attempts a purchase and fails,
possibly after taking a payment action on behalf of a user. The failure mode is
financial, not cosmetic. No amount of score improvement justifies publishing one
speculatively.

Specifications at this maturity also change in breaking ways. An implementation
written against an unverified draft is likely to be wrong within months, and
wrong in a way that is hard to detect from the outside.

## Applicability detection

Applicable when there is a payment dependency or real transaction code:

- payment SDKs such as Stripe, Braintree, PayPal, Adyen, Mollie, Square,
  Razorpay, Paddle, Lemon Squeezy;
- commerce platforms such as Shopify, WooCommerce, Medusa, Saleor, BigCommerce,
  Snipcart, Swell, Commerce.js;
- transaction code: checkout sessions, payment intents, cart mutations, order
  and line-item handling.

**Not** applicable from a pricing page, a products directory name, a contact
form, or marketing copy about paid services.

## If the site does transact

Report, in this order:

1. what commerce capability exists, with the evidence;
2. which protocols are in scope, and that each needs specification verification;
3. that structured Product and Offer data describing genuinely visible products
   is the useful, safe step available today, covered in
   [../../aeo-answerability/references/entities.md](../../aeo-answerability/references/entities.md);
4. that clear, server-rendered pricing and availability help agents far more than
   an unverified protocol declaration.

## Never

- Implement a payment protocol to improve a score.
- Create, expose or modify payment credentials, keys or webhooks.
- Change checkout, pricing or order logic during an AEO audit.
- Declare a commerce capability the site cannot honour.
