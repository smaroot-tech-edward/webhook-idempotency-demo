"""Runnable Smaroot demonstration using fictional inputs and a local SQLite CRM model."""
import hashlib
import json
import sqlite3
import tempfile
from pathlib import Path


def ingest(db_path, event):
    required = ("source", "submission_id", "name", "email")
    if any(not isinstance(event.get(k), str) or not event[k].strip() for k in required):
        return "invalid"
    normalized = {k: event[k].strip() for k in required}
    digest = hashlib.sha256(json.dumps(normalized, sort_keys=True).encode()).hexdigest()
    with sqlite3.connect(db_path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS leads (source TEXT, submission_id TEXT, name TEXT, email TEXT, payload_hash TEXT, UNIQUE(source, submission_id))")
        db.execute("BEGIN IMMEDIATE")
        prior = db.execute("SELECT payload_hash FROM leads WHERE source=? AND submission_id=?", (normalized["source"], normalized["submission_id"])).fetchone()
        if prior:
            return "duplicate_ignored" if prior[0] == digest else "conflict_requires_review"
        db.execute("INSERT INTO leads VALUES (?,?,?,?,?)", tuple(normalized[k] for k in required) + (digest,))
        return "created"


def main():
    output = Path(__file__).parent
    a = {"source": "website-form", "submission_id": "demo-001", "name": "Demo buyer A", "email": "buyer-a@example.com"}
    b = {"source": "website-form", "submission_id": "demo-002", "name": "Demo buyer B", "email": "buyer-b@example.com"}
    deliveries = [a, a.copy(), b]
    with tempfile.TemporaryDirectory(prefix="smaroot-webhook-demo-") as tmp:
        db_path = Path(tmp) / "crm.sqlite"
        outcomes = [ingest(db_path, x) for x in deliveries]
        retry_after_reopen = ingest(db_path, a)
        conflicting = ingest(db_path, {**a, "email": "changed@example.com"})
        invalid = ingest(db_path, {"source": "website-form"})
        with sqlite3.connect(db_path) as db:
            rows = db.execute("SELECT source,submission_id,name,email FROM leads ORDER BY submission_id").fetchall()
        checks = {
            "three_deliveries_create_two_leads": len(rows) == 2 and outcomes == ["created", "duplicate_ignored", "created"],
            "retry_after_reopen_is_ignored": retry_after_reopen == "duplicate_ignored",
            "changed_payload_not_silently_overwritten": conflicting == "conflict_requires_review" and rows[0][3] == a["email"],
            "incomplete_input_rejected": invalid == "invalid",
        }
        assert all(checks.values()), checks
        report = {"demonstration": "Smaroot fictional form-to-CRM webhook deduplication", "scope": "local SQLite CRM model; no real CRM, customer system or production use", "input_deliveries": deliveries, "naive_append_rows": len(deliveries), "fixed_rows": len(rows), "outcomes": outcomes, "retry_after_reopen": retry_after_reopen, "conflicting_replay": conflicting, "invalid_input": invalid, "checks": checks, "crm_rows": rows}
    (output / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"checks_passed": len(checks), "naive_rows": 3, "fixed_rows": 2, "result": str(output / "result.json")}))


if __name__ == "__main__":
    main()
