# CHANGE-PTP-2026-02 — Candidate Correction Note
Human-proposed correction for demonstration: introduce an idempotency-key check before any PTP state mutation. If an event key has already been processed, return the existing state and do not apply another transition. This note is a candidate correction until approved through CREED governance.
