# RECALL-PTP-V2-001 — Post-Adoption Regression Evidence
Synthetic post-adoption regression evidence for the optional CREED recall extension.

The PTP-EVENT-v2 idempotency implementation derives its replay key from an upstream request identifier that can be reused across two distinct Promise-to-Pay updates after a gateway recovery. In regression testing, the second legitimate update was incorrectly treated as a duplicate and suppressed. The observed behavior means the approved v2 guardrail is not safe for continued reuse until the key derivation rule is corrected and revalidated.
