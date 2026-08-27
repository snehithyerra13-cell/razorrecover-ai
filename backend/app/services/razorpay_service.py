import razorpay
import hmac
import hashlib
from app.config import settings

# Initialize official Razorpay SDK client if keys are present
razorpay_client = None
if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
    try:
        razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        # Use sandbox mode if possible (configured via key prefix e.g., rzp_test)
        print("Razorpay client successfully initialized in sandbox/test mode.")
    except Exception as e:
        print(f"Failed to initialize Razorpay SDK: {e}. Falling back to simulator mode.")
else:
    print("Razorpay keys not configured. Running in simulated Sandbox mode.")

def simulate_payment_retry(payment_id: str, failure_category: str) -> dict:
    """
    Simulates a payment retry on Razorpay Sandbox.
    Transient errors have a high chance of succeeding on retry.
    """
    import random
    
    # Determine retry outcome based on category
    if failure_category in ["TEMPORARY_BANK_FAILURE", "NETWORK_FAILURE", "TIMEOUT"]:
        # 85% success probability for transient errors
        success = random.random() < 0.85
        status = "SUCCESS" if success else "FAILED"
        err_code = None if success else "bad_request"
        err_desc = None if success else "Transaction declined by the cardholder bank during retry."
    elif failure_category == "INSUFFICIENT_FUNDS":
        # 25% chance customer added money quickly or retry went through
        success = random.random() < 0.25
        status = "SUCCESS" if success else "FAILED"
        err_code = None if success else "insufficient_funds"
        err_desc = None if success else "Insufficient funds in customer account."
    else:
        status = "FAILED"
        err_code = "permanent_error"
        err_desc = "Retry blocked: permanent card failure."

    return {
        "success": status == "SUCCESS",
        "status": status,
        "razorpay_payment_id": f"pay_test_ret_{random.randint(100000, 999999)}",
        "error_code": err_code,
        "error_reason": err_desc
    }

def generate_simulated_payment_link(payment_id: str, amount: float) -> str:
    """
    Generates a mock Razorpay Payment Link for updating payment credentials or retrying manually.
    """
    import random
    return f"https://api.razorpay.com/v1/paylinks/plink_demo_{random.randint(100000, 999999)}?payment_id={payment_id}&amt={amount}"

def verify_razorpay_signature(payload: str, signature: str, secret: str) -> bool:
    """
    Verifies the authenticity of a Razorpay webhook payload signature.
    """
    if not secret:
        return True # Fallback for local testing if webhook secret is not set
        
    try:
        # standard HMAC-SHA256 verification
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        print(f"Error verifying Razorpay signature: {e}")
        return False
