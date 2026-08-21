from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADVANCED = ROOT / "backend" / "app" / "services" / "advanced.py"
FRONT_API = ROOT / "frontend" / "lib" / "api.ts"
SHELL = ROOT / "frontend" / "components" / "analysis-shell.tsx"
CSS = ROOT / "frontend" / "app" / "globals.css"
TEST = ROOT / "backend" / "tests" / "test_r94_m07_adoption_receipt_visibility.py"


def require(text: str, needle: str) -> None:
    if needle not in text:
        raise SystemExit(f"FAIL: missing R94-M07 contract: {needle}")


def main() -> None:
    advanced = ADVANCED.read_text(encoding="utf-8")
    front_api = FRONT_API.read_text(encoding="utf-8")
    shell = SHELL.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    test = TEST.read_text(encoding="utf-8")

    for needle in (
        'receipt=db.scalar(select(AdoptionReceipt).where(AdoptionReceipt.learning_id==p.id))',
        '"adoption_receipt":serialize_receipt(db,receipt.id) if receipt else None',
        '"integrity": "VALID" if canonical_hash(d.receipt_payload_json)==r.content_hash else "INVALID"',
    ):
        require(advanced, needle)

    for needle in (
        "export type AdoptionReceiptSummary",
        "adoption_receipt: AdoptionReceiptSummary | null",
        "export type AdoptionReceiptVerification",
        "verifyAdoptionReceipt",
        "/adoption-receipts/${encodeURIComponent(receiptId)}/verify",
    ):
        require(front_api, needle)

    for needle in (
        "SIGNED ADOPTION RECEIPT",
        "Verify receipt",
        "SHA-256 verification passed",
        "Approved learning has no Adoption Receipt",
        "No Adoption Receipt was created",
        "learning.adoption_receipt",
    ):
        require(shell, needle)

    require(css, "R94-M07 — Signed Adoption Receipt Visibility & Integrity Proof")
    require(test, "test_approved_learning_embeds_signed_receipt_and_survives_refresh")
    require(test, "test_rejected_learning_has_no_adoption_receipt")
    print("R94-M07 source contract: PASS")


if __name__ == "__main__":
    main()
