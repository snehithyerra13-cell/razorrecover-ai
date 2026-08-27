import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

# Categorical Mappings
FAILURE_CATEGORIES = {
    "TEMPORARY_BANK_FAILURE": 0,
    "NETWORK_FAILURE": 1,
    "TIMEOUT": 2,
    "INSUFFICIENT_FUNDS": 3,
    "EXPIRED_CARD": 4,
    "INVALID_CARD": 5,
    "CUSTOMER_ACTION_REQUIRED": 6,
    "DUPLICATE_PAYMENT": 7,
    "PERMANENT_FAILURE": 8,
    "UNKNOWN": 9
}

PAYMENT_METHODS = {
    "card": 0,
    "upi": 1,
    "netbanking": 2,
    "wallet": 3
}

def generate_synthetic_data(n_samples=10000):
    np.random.seed(42)
    
    # Generate random features
    categories = np.random.choice(list(FAILURE_CATEGORIES.keys()), size=n_samples, p=[0.25, 0.15, 0.10, 0.20, 0.12, 0.05, 0.05, 0.03, 0.03, 0.02])
    methods = np.random.choice(list(PAYMENT_METHODS.keys()), size=n_samples, p=[0.4, 0.4, 0.15, 0.05])
    amounts = np.random.exponential(scale=3000, size=n_samples) + 100
    retry_counts = np.random.choice([0, 1, 2], size=n_samples, p=[0.7, 0.2, 0.1])
    customer_success_rates = np.random.uniform(0.1, 0.99, size=n_samples)
    
    # Recovery rule probabilities (simulate real-world patterns)
    probs = []
    for cat, method, amt, retry, success in zip(categories, methods, amounts, retry_counts, customer_success_rates):
        if cat == "TEMPORARY_BANK_FAILURE":
            base_prob = 0.85
        elif cat in ["NETWORK_FAILURE", "TIMEOUT"]:
            base_prob = 0.90
        elif cat == "INSUFFICIENT_FUNDS":
            base_prob = 0.45
        elif cat == "EXPIRED_CARD":
            base_prob = 0.25
        elif cat == "CUSTOMER_ACTION_REQUIRED":
            base_prob = 0.55
        elif cat in ["INVALID_CARD", "PERMANENT_FAILURE", "DUPLICATE_PAYMENT"]:
            base_prob = 0.01
        else:
            base_prob = 0.30
            
        retry_penalty = -0.15 * retry
        customer_bonus = 0.2 * (success - 0.5)
        amount_penalty = -0.05 if amt > 10000 else 0.0
        
        final_prob = np.clip(base_prob + retry_penalty + customer_bonus + amount_penalty, 0.0, 1.0)
        probs.append(final_prob)
        
    # Generate labels based on probabilities
    is_recovered = np.random.binomial(1, probs)
    
    # Map features to integers for scikit-learn
    cat_encoded = np.array([FAILURE_CATEGORIES[c] for c in categories])
    method_encoded = np.array([PAYMENT_METHODS[m] for m in methods])
    
    # Stack features horizontally to create X matrix (N, 5)
    X = np.column_stack((cat_encoded, method_encoded, amounts, retry_counts, customer_success_rates))
    y = is_recovered
    
    return X, y

def train_model():
    print("Generating synthetic data for model training...")
    X, y = generate_synthetic_data(10000)
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training RandomForest model...")
    model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model trained successfully! Accuracy: {accuracy:.4f}")
    
    # Save the model
    os.makedirs(os.path.dirname(__file__), exist_ok=True)
    model_path = os.path.join(os.path.dirname(__file__), "model.joblib")
    joblib.dump(model, model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train_model()
