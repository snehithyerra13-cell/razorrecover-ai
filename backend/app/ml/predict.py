import os
import joblib
import numpy as np
from app.ml.train import FAILURE_CATEGORIES, PAYMENT_METHODS, train_model

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")
_model = None

def get_model():
    global _model
    if _model is not None:
        return _model
    if not os.path.exists(MODEL_PATH):
        try:
            print("Model joblib not found. Training model on the fly...")
            train_model()
        except Exception as e:
            print(f"Error training model on the fly: {e}")
            return None
    try:
        _model = joblib.load(MODEL_PATH)
    except Exception as e:
        print(f"Error loading model: {e}")
        _model = None
    return _model

def predict_recovery_probability(
    failure_category: str,
    payment_method: str,
    amount: float,
    retry_count: int,
    customer_success_rate: float
) -> float:
    # Get encoded values, fallback to default if not found
    cat_val = FAILURE_CATEGORIES.get(failure_category, 9) # Default to UNKNOWN (9)
    method_val = PAYMENT_METHODS.get(payment_method, 0) # Default to card (0)
    
    model = get_model()
    if model is None:
        # Fallback to rule-based probability prediction if model cannot be loaded
        if failure_category == "TEMPORARY_BANK_FAILURE":
            base = 0.85
        elif failure_category in ["NETWORK_FAILURE", "TIMEOUT"]:
            base = 0.90
        elif failure_category == "INSUFFICIENT_FUNDS":
            base = 0.45
        elif failure_category == "EXPIRED_CARD":
            base = 0.25
        elif failure_category == "CUSTOMER_ACTION_REQUIRED":
            base = 0.55
        elif failure_category in ["INVALID_CARD", "PERMANENT_FAILURE", "DUPLICATE_PAYMENT"]:
            base = 0.01
        else:
            base = 0.30
        
        prob = base - 0.15 * retry_count + 0.2 * (customer_success_rate - 0.5)
        if amount > 10000:
            prob -= 0.05
        return float(np.clip(prob, 0.0, 1.0))
        
    try:
        # Features array shape: (1, 5)
        # Columns: failure_category, payment_method, amount, retry_count, customer_success_rate
        features = np.array([[cat_val, method_val, amount, retry_count, customer_success_rate]])
        # Predict probability of class 1 (recovered)
        prob = model.predict_proba(features)[0][1]
        return float(prob)
    except Exception as e:
        print(f"Prediction failed, using fallback: {e}")
        # Rule-based fallback
        if failure_category == "TEMPORARY_BANK_FAILURE":
            base = 0.85
        elif failure_category in ["NETWORK_FAILURE", "TIMEOUT"]:
            base = 0.90
        elif failure_category == "INSUFFICIENT_FUNDS":
            base = 0.45
        else:
            base = 0.30
        prob = base - 0.15 * retry_count + 0.2 * (customer_success_rate - 0.5)
        return float(np.clip(prob, 0.0, 1.0))
