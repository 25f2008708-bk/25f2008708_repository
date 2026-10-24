# Evidence-based Invoice Agent

A FastAPI starter that accepts invoice documents, uses an OpenAI-compatible model to extract facts, records evidence, applies deterministic policy checks, and stores action state in SQLite.

## Important: adapt the protocol before submitting to a grader

The task description alone does not specify the grader's endpoint contract, package retrieval API, action names, receipt schema, or Save protocol. This project exposes a generic API. Map the actual platform protocol to these routes before using it for a graded task. Do not claim compatibility until tested against the platform's official contract.

## Safety model

- The LLM only extracts structured facts and evidence excerpts; it cannot directly execute actions.
- Payment eligibility is checked by deterministic rules.
- Payment execution is disabled unless `ACTION_API_URL` is configured.
- The action provider must honor the `Idempotency-Key` header and return a real `receipt` or `receipt_id`.
- A timeout or missing receipt creates a reconciliation-required state; the agent does not blindly retry.
- State is persisted in SQLite. For a hosted multi-instance service, use durable storage or PostgreSQL and a transaction/locking strategy.
- This starter does not assume that an invoice is paid because a document says it was paid; integrate authoritative payment-status lookup for production.

## Run locally

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
```

Set environment variables (use your own secret values):

```bash
# macOS/Linux
export AGENT_API_KEY='replace-with-long-random-secret'
export LLM_API_KEY='your-provider-key'
export LLM_BASE_URL='https://api.openai.com/v1'
export LLM_MODEL='gpt-4o-mini'
export MAX_APPROVED_AMOUNT='1000'
uvicorn app:app --reload
```

PowerShell equivalents:
```powershell
$env:AGENT_API_KEY="replace-with-long-random-secret"
$env:LLM_API_KEY="your-provider-key"
$env:LLM_BASE_URL="https://api.openai.com/v1"
$env:LLM_MODEL="gpt-4o-mini"
uvicorn app:app --reload
```

Open `http://127.0.0.1:8000/docs`.

## API flow

All routes except `/` and `/health` require `Authorization: Bearer <AGENT_API_KEY>` when `AGENT_API_KEY` is set.

1. Upload one or more PDF/text documents:
   `POST /packages` with multipart field `files`.
2. If AI is unavailable, submit extracted facts:
   `POST /packages/{package_id}/facts`.
3. Evaluate deterministic rules:
   `POST /packages/{package_id}/decide` with `{"package_id":"...","execute":false}`.
4. Only after verifying the platform's approval protocol and configuring a genuine action adapter, use `execute:true`.
5. Inspect persisted results through `/packages/{id}`, `/invoices`, and `/actions`.

Example upload:
```bash
curl -X POST http://127.0.0.1:8000/packages \
  -H "Authorization: Bearer YOUR_SECRET" \
  -F "files=@invoice.pdf" -F "files=@approval.pdf"
```

Example decision:
```bash
curl -X POST http://127.0.0.1:8000/packages/PACKAGE_UUID/decide \
  -H "Authorization: Bearer YOUR_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"package_id":"PACKAGE_UUID","execute":false}'
```

## Public HTTPS deployment

1. Push this folder to a private Git repository.
2. Create a web service on Render (or another Python host) from that repository.
3. Use `pip install -r requirements.txt` as build command and `uvicorn app:app --host 0.0.0.0 --port $PORT` as start command.
4. Configure secrets as environment variables; never commit API keys.
5. Configure persistent disk at `/data` and set `DB_PATH=/data/invoice_agent.sqlite3`, or switch to managed PostgreSQL. Without durable storage, SQLite state may be lost on redeploy/restart.
6. Configure a genuine action API only after confirming its exact protocol. Use the platform's real receipt lookup endpoint to reconcile uncertain outcomes.
7. Test `/health` over the public HTTPS URL.

## Before grading

- Implement the exact endpoints, request/response JSON, action vocabulary, and final Save operation required by the grader.
- Use the grader's real invoice package source, not fabricated test documents.
- Cite real document excerpts and page numbers; validate that excerpts occur in the source.
- Define approval authority and limits from the task rules, not arbitrary defaults.
- Distinguish invoices by the required identity (usually supplier + invoice number or platform-provided invoice ID); never deduplicate on amount alone.
- Store provider receipt IDs and query the provider before retrying uncertain payments.
- Use idempotency keys supported by the payment provider. Local state alone cannot guarantee exactly-once payment if the remote provider lacks idempotency/reconciliation.
- Preserve the last check for Save as required by the platform.
