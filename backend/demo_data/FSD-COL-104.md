# FSD-COL-104 — Promise-to-Pay Event Processing
Product: Collections
Module: Promise-to-Pay
Method: PTP-EVENT-v1

PTP events transition through PROPOSED, ACTIVE, BROKEN or COMPLETED. Version 1 processes an accepted event as a state mutation. Duplicate and out-of-order delivery must be considered by client-specific implementation controls. The baseline v1 functional specification does not itself define a mandatory idempotency-key guard.
