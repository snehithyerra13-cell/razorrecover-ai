# Hackathon Demo Guide - RazorRecover AI

Follow this 5-minute walkthrough to demonstrate the full capabilities of RazorRecover AI during hackathon evaluation.

---

## The Demo Scenario
We demonstrate recovery on a high-value customer payment that failed due to a **temporary bank gateway error**. 

### Step 1: Open the Dashboard
1. Navigate to the web application at [http://localhost:5173](http://localhost:5173).
2. The dashboard shows aggregate business metrics: **Total Transactions**, **Failed Payments**, **Revenue at Risk**, **Revenue Recovered**, and the **Recovery Rate**. All values are calculated dynamically from the SQLite ledger.
3. Click the **Reset & Seed Demo Data** button in the header. This resets the SQLite database and generates fresh transaction history (including past successful recoveries to populate the analytics gauges).

---

### Step 2: Select the Evaluation Transaction
1. In the payments table, locate the pinned transaction:
   - **ID**: `pay_demo_123`
   - **Amount**: `₹4,999`
   - **Failure Category**: `Temporary Bank Failure`
   - **Status**: `FAILED`
   - **Retry Count**: `0/3`
2. Click the **Analyze** button on that row. The app redirects to the transaction detail workspace.

---

### Step 3: Run AI and ML Analysis
1. In the **Plan & Policy** panel, click the **Analyze Transaction** button.
2. The backend performs the following actions:
   - Computes customer success rate from historical transactions.
   - Feeds checkout features into the local **RandomForest** model, returning a **91% recovery probability score**.
   - Queries the **AI Recovery Agent** (using Gemini API or rule-based fallback) to formulate a recovery plan.
   - Evaluates the AI decision (`RETRY_AFTER_DELAY`) against the deterministic **Policy Engine** safety rules.
3. Observe the output:
   - **AI Strategy**: `RETRY`
   - **Policy Engine**: `APPROVED BY POLICY`
   - **ML Score**: `91%` (High confidence)
   - **Chronological timeline**: New audit logs for `AI_DECISION_CREATED` and `POLICY_CHECKED` appear instantly.

---

### Step 4: Execute Recovery and Recover Revenue
1. Click the **Execute Recovery** button.
2. The backend Executor executes the retry action, simulating a connection to Razorpay Sandbox. 
3. The mock transaction succeeds! The app UI displays:
   - **Status Badge** transitions to `RECOVERED` (green).
   - A new audit ledger record: `RECOVERY_SUCCEEDED`.
4. Click **Back to Dashboard** in the top left.
5. Notice that:
   - **Revenue Recovered** has increased by `₹4,999`.
   - **Revenue at Risk** remains the same, but the **Remaining Risk** has decreased.
   - **Recovery Rate** increases.
