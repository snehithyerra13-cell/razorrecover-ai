# API Documentation - RazorRecover AI

The backend REST API is built with FastAPI. By default, it runs on `http://localhost:8000`.

Interactive documentation (Swagger UI) is available at `/docs`.

---

## 1. Health Checks
### `GET /api/health`
Checks backend database and service status.

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "service": "razorrecover-api"
}
```

---

## 2. Seed Database
### `POST /api/demo/seed`
Wipes the local database ledger and seeds it with fresh synthetic checkout events (both successes and failures).

**Query Parameters**:
- `n_payments` (int, default=150): The number of transactions to generate.

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Successfully seeded database with demo transactions.",
  "merchant_id": "96b6b7a9-9e8c-4a3b-9e4a-81f7c1971bd6"
}
```

---

## 3. Payments Audit Ledger
### `GET /api/payments`
Returns a list of payment records, ordered by creation date descending.

**Query Parameters**:
- `status` (string, optional): Filter by `SUCCESS`, `FAILED`, `RECOVERING`, or `RECOVERED`.
- `search` (string, optional): Match customer email, reference, or payment IDs.

**Response (200 OK)**:
```json
[
  {
    "id": "pay_demo_123",
    "merchant_id": "96b6b7a9-9e8c-...",
    "amount": 4999.00,
    "payment_method": "card",
    "status": "FAILED",
    "failure_category": "TEMPORARY_BANK_FAILURE",
    "retry_count": 0,
    "created_at": "2026-08-27T10:00:00",
    "customer": {
      "customer_reference": "cust_demo_101",
      "email": "rahul.sharma87@gmail.com"
    }
  }
]
```

---

## 4. Transaction Details
### `GET /api/payments/{id}`
Returns full detail for a single transaction including previous recovery attempts, notifications sent, and policy decisions.

---

## 5. Recovery Workflows
### `POST /api/payments/{id}/analyze`
Triggers AI classification and recovery planning. Uses the ML Random Forest model to compute probability of recovery and queries the Gemini LLM for custom action planning. Validates outcomes against safety rules.

**Response (200 OK)**:
```json
{
  "payment_id": "pay_demo_123",
  "failure_category": "TEMPORARY_BANK_FAILURE",
  "recovery_probability": 0.91,
  "ai_decision": "RETRY",
  "explanation": "Payment failed due to temporary bank gate error. ML models recommend retry with 91% success rate. Approved by policy rules.",
  "policy_result": "APPROVED",
  "confidence": 0.91
}
```

### `POST /api/payments/{id}/recover`
Executes the recovery strategy approved in the latest analysis. Auto-retries payments (transient errors), fires notifications (insufficient funds), or routes links (expired cards).

**Response (200 OK)**:
```json
{
  "payment_id": "pay_demo_123",
  "success": true,
  "status": "SUCCESS",
  "action_executed": "RETRY",
  "recovered_amount": 4999.00,
  "message": "Action 'RETRY' executed. Result status: SUCCESS."
}
```
