# RazorRecover AI

**An autonomous, policy-controlled AI agent that identifies recoverable payment failures, predicts recovery probability, chooses the best recovery strategy, executes bounded recovery actions, and measures the revenue actually recovered.**

*Built for the Razorpay Buildathon.*

---

## 1. Problem Statement
Every year, merchants lose millions in transaction volume due to failed payments. However, not all payment failures are created equal:
- Transient errors (e.g. temporary bank downtimes, network failures) can succeed if retried after a brief delay.
- User-actionable errors (e.g. insufficient funds, incorrect OTP) require prompting the customer.
- Card credentials errors (e.g. expired cards) require giving the customer a secure link to update payment methods.
- Permanent errors (e.g. invalid cards, duplicates) should be stopped immediately to prevent merchant fee build-up and protect against fraud.

Without an intelligent system, merchants treat all failures identically, leading to high friction, wasted fees, cardholder annoyance, and substantial revenue leakage.

---

## 2. The Solution: RazorRecover AI
RazorRecover AI acts as an autonomous revenue guard for merchants:
1. **Frictionless Webhook Intake**: Captures failure checkout payloads from Razorpay.
2. **Deterministic Failure Classification**: Standardizes error codes into failure classes.
3. **ML Prediction Model**: Uses a custom-trained RandomForest model to estimate recovery probability.
4. **AI Recovery Agent**: Employs LLM intelligence to plan optimal recovery actions based on failure context.
5. **Deterministic Policy Guards**: Subjects the AI decision to safety checks (retry thresholds, amount validation).
6. **Execution Engine**: Executes the action in the Razorpay Sandbox environment.
7. **Business Ledger Audit**: Logs all steps immutably for merchants and reports business metrics dynamically.

---

## 3. Technology Stack
- **Backend**: Python (FastAPI), SQLAlchemy (SQLite), Pydantic
- **Machine Learning**: Scikit-Learn (Random Forest)
- **AI Agent**: Google Gemini SDK (with local rule-based fallback)
- **Fintech Integration**: Official Razorpay Python SDK / Simulated Sandbox
- **Frontend**: React, TypeScript, Tailwind CSS, Lucide Icons

---

## 4. Repository Structure
```
razorrecover-ai/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI Routes (payments, health, analytics, seed)
│   │   ├── db/           # SQLite Database Session and Demo Seed Scripts
│   │   ├── models/       # SQLAlchemy ORM Tables
│   │   ├── schemas/      # Pydantic Schemas
│   │   ├── ml/           # Model Training and Prediction Engines
│   │   ├── agents/       # Gemini AI Agent prompt flows
│   │   ├── policies/     # Deterministic safety rule checks
│   │   └── services/     # Sandbox executor and Razorpay API wrappers
│   ├── tests/            # Pytest Unit and Integration Tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── services/     # Axios/Fetch API wrapper
│   │   ├── types/        # TypeScript Definitions
│   │   ├── App.tsx       # Interactive Dashboard Workspace UI
│   │   └── index.css     # Glassmorphic Dark styling
│   ├── package.json
│   └── tailwind.config.js
├── docs/                 # Architectural specifications and diagrams
├── .env.example
├── docker-compose.yml
└── README.md
```

---

## 5. Setup & Running Locally

Please refer to the detailed [Setup Guide](file:///docs/setup.md) for full configuration.

### Short Version:

1. **Clone the repository**:
   ```bash
   git clone <repository_url>
   cd razorrecover-ai
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   ```
   Add your `GEMINI_API_KEY` (optional; falls back to rules) and `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET`.

3. **Install and Run Backend**:
   ```bash
   cd backend
   python -m venv venv
   # Activate venv: .\venv\Scripts\Activate.ps1 (Windows) or source venv/bin/activate (UNIX)
   pip install -r requirements.txt
   python app/ml/train.py   # Train the ML model
   uvicorn app.main:app --reload
   ```

4. **Install and Run Frontend**:
   ```bash
   cd ../frontend
   yarn install
   yarn dev
   ```
   Open [http://localhost:5173](http://localhost:5173).

---

## 6. Running Tests
Run backend unit tests for the Policy Engine and ML model prediction outputs:
```bash
cd backend
pytest tests/
```

---

## 7. High-Fidelity Demo Scenario
The application features a built-in evaluation workspace designed for hackathon judges:
1. Open the dashboard and click **Reset & Seed Demo Data** to populate the ledger.
2. Locate the failed payment **`pay_demo_123`** (Amount: `₹4,999`, Type: `Temporary Bank Failure`) in the list.
3. Click **Analyze** to open the details workspace.
4. Click **Analyze Transaction** to watch the ML model predict a **91% recovery rate** and Gemini formulate a `RETRY` plan approved by the Policy Engine.
5. Click **Execute Recovery** to run the mock sandbox retry. The payment badge updates to `RECOVERED`, ₹4,999 is added to the dynamic **Revenue Recovered** metric, and the ledger updates immutably.
