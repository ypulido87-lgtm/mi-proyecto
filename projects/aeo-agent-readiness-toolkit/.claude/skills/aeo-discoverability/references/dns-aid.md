# DNS-AID reporting template

DNS-AID proposes publishing AI-agent discovery information in DNS. It is pre-1.0.

**This toolkit never modifies DNS.** Zone changes affect mail delivery, TLS
issuance and site availability, they are frequently controlled by someone other
than the person requesting the audit, and a mistake is disruptive and slow to
detect. Diagnose, hand over instructions, and stop.

## Before proposing anything

Verify the current specification. If the record name, value format or semantics
cannot be confirmed against primary documentation, report:

```
DNS-AID: MANUAL REVIEW — specification could not be verified. No record proposed.
```

Do not guess a record format. A malformed TXT record published at a well-known
name is a false signal that costs real DNS operations effort to remove.

## Report template

```
### DNS-AID

Status: MANUAL REVIEW
Specification verified: <yes/no> (<source URL>, checked <date>)

Diagnosis
  Current state:        <no record found / record present but unverified>
  Zone:                 <example.com>
  Zone owner:           <who controls DNS — registrar, hosting provider, IT team>

Proposed record
  Name:                 <exact record name, only if the spec was verified>
  Type:                 <TXT / other, per the specification>
  Value:                <exact value, only if the spec was verified>
  TTL:                  <recommended TTL>

Implementation
  1. The zone owner adds the record in the DNS provider's control panel.
  2. Wait for propagation (up to the previous TTL).
  3. Do not remove or modify existing records.

Verification
  dig +short TXT <record name>
  nslookup -type=TXT <record name>
  Confirm the value matches exactly and that no other record was affected.

Rollback
  Delete the added record. No other change was made.
```

## What counts as done

DNS-AID is never `PASS` on the strength of a repository file — DNS is not in the
repository. It is `PASS` only when a record is observed and verified against a
confirmed specification. Otherwise it stays `MANUAL REVIEW` and appears under
Remaining Manual Actions.
