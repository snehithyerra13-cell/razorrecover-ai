# Architectural Decisions - RazorRecover AI

This document outlines the rationale behind key technical choices made during the development of RazorRecover AI.

---

## 1. Database Choice: SQLite
- **Decision**: Use SQLite for local development and demonstration.
- **Rationale**:
  - Eliminates external dependencies (no docker configuration, database user creation, or port collisions for judges).
  - Offers zero-configuration deployment; the SQLite file is created automatically on application startup.
  - Fully supports modern SQL queries, aggregates (e.g. `SUM`, `COUNT`), and transactions via SQLAlchemy ORM.

---

## 2. ML Stack: RandomForest Classifier via Scikit-Learn
- **Decision**: Avoid complex Deep Learning frameworks (TensorFlow, PyTorch) in favor of standard Scikit-Learn models.
- **Rationale**:
  - Random Forests are fast to train (seconds), lightweight, and easily serializable using `joblib`.
  - Native Windows binary wheels exist for Python 3.13, ensuring compiler-free installations on judge environments.
  - Generates highly interpretable feature importances, aligning with the "AI Explainability" hackathon requirement.

---

## 3. AI Agent Architecture: LLM with Rule-Based Fallback
- **Decision**: Integrate official Google Gemini SDK but bundle a robust rule-based model fallback.
- **Rationale**:
  - Guarantees the application remains 100% functional out-of-the-box even without a configured `GEMINI_API_KEY`.
  - Standardizes the response format via JSON schemas, protecting the parsing layer from AI hallucinations.

---

## 4. Policy Engine: Hard Deterministic Guardrails
- **Decision**: Keep the Safety & Policy Engine completely decoupled from the AI LLM layer and write it in deterministic Python code.
- **Rationale**:
  - LLMs are probabilistic and prone to prompt injections or formatting deviations.
  - In financial and fintech scenarios, allowing an AI agent to perform transactions unchecked is a severe security risk.
  - Decoupling ensures that even if the AI recommends a malicious or incorrect action (e.g., retrying an expired card 100 times), the policy engine catches and blocks it before reaching the payment processor.
