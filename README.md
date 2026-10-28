# One submission, one CRM lead

A form integration can receive the same webhook more than once. Creating a new CRM record on every delivery can leave sales teams with duplicate leads.

This runnable Smaroot example sends three deliveries containing two unique submissions. A persistent `source + submission_id` key keeps two records. Replaying the same event after reopening the database does not create another lead. If the same key arrives with different content, the example flags a conflict rather than overwriting the existing record.

## Run

Requires Python 3 and its standard library; no account, token, network request or paid service is used.

```sh
python3 demo.py
```

The command writes `result.json` beside the script. The four acceptance checks cover:

1. Three deliveries create two unique leads.
2. Replaying an event after reconnecting remains safe.
3. Changed content for an existing key is flagged without overwriting the lead.
4. Missing required fields are rejected.

All inputs are fictional. The implementation demonstrates a local SQLite CRM model; it does not claim a client deployment, third-party CRM integration, concurrent-load validation or measured business savings.

For an actual integration, we first identify the event key, destination fields, retry rules and acceptance checks. [Describe your workflow](https://www.smaroot.tech/?utm_source=github&utm_medium=case_study&utm_campaign=webhook_dedup).
