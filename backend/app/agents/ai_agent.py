import os
import json
import google.generativeai as genai
from app.config import settings

# Initialize Gemini if key is provided
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

def run_rule_fallback(failure_category: str, payment_method: str, amount: float, retry_count: int, recovery_probability: float) -> dict:
    """Deterministic fallback rules for AI analysis when Gemini API is not configured or fails."""
    
    if failure_category == "TEMPORARY_BANK_FAILURE":
        decision = "RETRY"
        strategy = "RETRY_AFTER_DELAY"
        delay_minutes = 30
        explanation = (
            f"The payment failed due to a temporary bank issue. "
            f"ML model predicts a high recovery probability of {recovery_probability:.0%}. "
            f"Retrying after 30 minutes gives the bank system time to stabilize."
        )
    elif failure_category in ["NETWORK_FAILURE", "TIMEOUT"]:
        decision = "RETRY"
        strategy = "RETRY_AFTER_DELAY"
        delay_minutes = 15
        explanation = (
            f"A network timeout occurred during checkout. "
            f"Recovery probability is {recovery_probability:.0%}. "
            f"A quick 15-minute delayed automatic retry is recommended to handle transient connectivity drops."
        )
    elif failure_category == "INSUFFICIENT_FUNDS":
        decision = "NOTIFY_CUSTOMER"
        strategy = "SMS_NOTIFICATION"
        delay_minutes = 0
        explanation = (
            f"Payment declined due to insufficient balance. "
            f"Recovery probability is {recovery_probability:.0%}. "
            f"We recommend notifying the customer via SMS/WhatsApp so they can add funds or select another payment method."
        )
    elif failure_category == "EXPIRED_CARD":
        decision = "REQUEST_PAYMENT_UPDATE"
        strategy = "UPDATE_CARD_LINK"
        delay_minutes = 0
        explanation = (
            f"The transaction failed because the customer's card is expired. "
            f"Recovery probability is {recovery_probability:.0%}. "
            f"Direct automatic retries will fail. We must send a secure link to update payment methods."
        )
    elif failure_category == "CUSTOMER_ACTION_REQUIRED":
        decision = "NOTIFY_CUSTOMER"
        strategy = "EMAIL_NOTIFICATION"
        delay_minutes = 0
        explanation = (
            f"Customer action is required to complete authentication (e.g. incorrect OTP or PIN). "
            f"Recovery probability is {recovery_probability:.0%}. "
            f"Sending a drop-off recovery email will prompt the user to re-initiate the payment."
        )
    elif failure_category in ["INVALID_CARD", "PERMANENT_FAILURE", "DUPLICATE_PAYMENT"]:
        decision = "STOP"
        strategy = "NO_ACTION"
        delay_minutes = 0
        explanation = (
            f"This is a permanent failure (invalid credentials or duplicate payment). "
            f"Recovery probability is extremely low ({recovery_probability:.0%}). "
            f"We must stop further recovery attempts to avoid merchant fraud triggers and fee accumulation."
        )
    else:
        decision = "NO_ACTION"
        strategy = "NO_ACTION"
        delay_minutes = 0
        explanation = (
            f"The failure category is unknown or unhandled. "
            f"Recovery probability is {recovery_probability:.0%}. "
            f"We suggest holding action for review."
        )
        
    return {
        "decision": decision,
        "strategy": strategy,
        "delay_minutes": delay_minutes,
        "confidence": float(recovery_probability),
        "explanation": explanation
    }

def analyze_failed_payment(
    failure_category: str,
    payment_method: str,
    amount: float,
    retry_count: int,
    recovery_probability: float,
    customer_history: str = ""
) -> dict:
    """
    Invokes the AI Recovery Agent.
    If GEMINI_API_KEY is available, uses Gemini. Otherwise, falls back to deterministic rule engine.
    """
    if not settings.GEMINI_API_KEY:
        return run_rule_fallback(failure_category, payment_method, amount, retry_count, recovery_probability)
        
    # Configure Gemini prompt
    prompt = f"""
    You are RazorRecover AI, an autonomous payment recovery agent.
    A customer transaction failed, and we need your recommendation on the best recovery strategy.

    Transaction Details:
    - Failure Category: {failure_category}
    - Payment Method: {payment_method}
    - Amount: INR {amount:.2f}
    - Retry Count so far: {retry_count}
    - ML Predicted Recovery Probability: {recovery_probability:.0%}
    - Customer Payment History Context: {customer_history}

    Your decision must be one of:
    - "RETRY": For transient errors (bank downtime, network timeout) where retrying later works.
    - "NOTIFY_CUSTOMER": For user-correctable issues like insufficient funds, prompting them to refill/retry.
    - "REQUEST_PAYMENT_UPDATE": For expired cards or blocked cards, asking them to enter a new payment method.
    - "ESCALATE": For high-value transactions with persistent errors requiring manual support intervention.
    - "STOP": For invalid cards, duplicate payments, or when retry limits are exceeded.
    - "NO_ACTION": Default when no recovery is possible.

    Your strategy should name the method (e.g. "RETRY_AFTER_DELAY", "SMS_NOTIFICATION", "UPDATE_CARD_LINK", "MANUAL_SUPPORT").
    If RETRY, suggest delay_minutes (integer, e.g. 15, 30, 60, 1440). Otherwise, set delay_minutes to 0.

    Provide a human-readable explanation justifying your decision based on the failure category, transaction amount, and probability. Keep the explanation concise (2-3 sentences max) and suitable for a merchant dashboard.

    Respond ONLY with a JSON object containing these keys:
    {{
        "decision": "RETRY" | "NOTIFY_CUSTOMER" | "REQUEST_PAYMENT_UPDATE" | "ESCALATE" | "STOP" | "NO_ACTION",
        "strategy": "string",
        "delay_minutes": int,
        "confidence": float,
        "explanation": "string"
    }}
    """
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        data = json.loads(response.text.strip())
        return data
    except Exception as e:
        print(f"Gemini API call failed, falling back to rules. Error: {e}")
        return run_rule_fallback(failure_category, payment_method, amount, retry_count, recovery_probability)
