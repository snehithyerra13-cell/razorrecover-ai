import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.models import Merchant, Customer, Payment, AuditLog, RecoveryDecision, RecoveryAttempt
from app.ml.train import FAILURE_CATEGORIES

# Failure classifications list for random selection
FAILURE_TYPES = [
    ("TEMPORARY_BANK_FAILURE", "bank_failure", "Transaction failed due to internal bank gateway downtime."),
    ("NETWORK_FAILURE", "network_error", "A network handshake timeout occurred with the processor."),
    ("TIMEOUT", "gateway_timeout", "The payment request timed out at the payment gateway."),
    ("INSUFFICIENT_FUNDS", "insufficient_funds", "The account has insufficient balance to complete the transaction."),
    ("EXPIRED_CARD", "expired_card", "The card expiration date is in the past."),
    ("INVALID_CARD", "invalid_card_number", "The card number is invalid or checksum failed."),
    ("CUSTOMER_ACTION_REQUIRED", "incorrect_pin", "Authentication failed. Incorrect PIN or OTP entered."),
    ("DUPLICATE_PAYMENT", "duplicate_payment", "Duplicate payment attempt detected for this order."),
    ("PERMANENT_FAILURE", "card_blocked", "The card has been blocked by the issuing bank."),
    ("UNKNOWN", "unknown_error", "An unclassified failure occurred during authorization.")
]

def seed_database_demo_data(db: Session, n_payments: int = 150):
    """
    Seeds the database with a high-fidelity synthetic dataset.
    This creates:
    - 1 Merchant
    - 20-30 Customers with varied historical success rates
    - A set of payments (approx 70% success, 30% failure)
    - Pre-computed failure classifications and audit logs.
    """
    # 1. Create Merchant if not present
    merchant = db.query(Merchant).filter(Merchant.email == "demo@merchant.com").first()
    if not merchant:
        merchant = Merchant(
            name="RazorRecover Demo Merchant",
            email="demo@merchant.com"
        )
        db.add(merchant)
        db.commit()
        db.refresh(merchant)
        print(f"Created merchant: {merchant.name}")
    
    # Check if we already have payments. If yes, skip seeding to avoid duplicate data.
    existing_payments = db.query(Payment).filter(Payment.merchant_id == merchant.id).count()
    if existing_payments > 50:
        print(f"Database already has {existing_payments} payments. Skipping seeding.")
        return merchant.id

    # 2. Create Customers
    customers = []
    first_names = ["Rahul", "Priya", "Amit", "Sneha", "Vikram", "Anjali", "Rohan", "Neha", "Aditya", "Pooja", "Arjun", "Kiran"]
    last_names = ["Sharma", "Verma", "Patel", "Nair", "Singh", "Gupta", "Mehta", "Rao", "Joshi", "Das", "Reddy", "Choudhury"]
    
    for i in range(30):
        ref_id = f"cust_demo_{100 + i}"
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        customer = Customer(
            merchant_id=merchant.id,
            customer_reference=ref_id,
            email=f"{fn.lower()}.{ln.lower()}{random.randint(10,99)}@gmail.com",
            phone=f"+91{random.randint(7000000000, 9999999999)}"
        )
        db.add(customer)
        customers.append(customer)
    db.commit()
    print("Created 30 demo customers.")

    # 3. Create Payments (going back 30 days)
    methods = ["card", "upi", "netbanking", "wallet"]
    method_probs = [0.45, 0.40, 0.10, 0.05]
    
    base_date = datetime.utcnow()
    
    # We want a special mock payment for the JUDGE demo: Transaction #pay_demo_123
    # Temporary bank failure, amount 4999, status failed, retry_count 0.
    judge_customer = customers[0]
    judge_payment = Payment(
        id="pay_demo_123",
        merchant_id=merchant.id,
        customer_id=judge_customer.id,
        razorpay_payment_id="pay_RZP_judge_init",
        amount=4999.00,
        currency="INR",
        payment_method="card",
        status="FAILED",
        failure_code="bank_failure",
        failure_reason="Transaction failed due to internal bank gateway downtime.",
        failure_category="TEMPORARY_BANK_FAILURE",
        retry_count=0,
        created_at=base_date - timedelta(minutes=10),
        updated_at=base_date - timedelta(minutes=10)
    )
    db.add(judge_payment)
    db.commit()
    
    # Audit log for judge payment
    audit_init = AuditLog(
        payment_id=judge_payment.id,
        action="PAYMENT_FAILED",
        actor="RAZORPAY_SERVICE",
        reason="Initial payment authorization failed with code: bank_failure.",
        metadata_json='{"error_code": "bank_failure", "gateway": "HDFC"}',
        timestamp=judge_payment.created_at
    )
    db.add(audit_init)
    db.commit()

    payments_seeded = 1
    
    # Generate the rest of the payments
    for i in range(n_payments):
        cust = random.choice(customers)
        amt = float(random.randint(199, 15000))
        method = random.choice(methods) # or numpy choice but random is fine for seed
        # Weighted choice for method
        method = random.choices(methods, weights=method_probs)[0]
        
        # 75% success, 25% failure
        is_success = random.random() < 0.75
        status = "SUCCESS" if is_success else "FAILED"
        
        # Payment date spread over 30 days
        days_ago = random.uniform(0.1, 30.0)
        pay_date = base_date - timedelta(days=days_ago)
        
        pay = Payment(
            merchant_id=merchant.id,
            customer_id=cust.id,
            razorpay_payment_id=f"pay_RZP_{random.randint(100000000, 999999999)}",
            amount=amt,
            currency="INR",
            payment_method=method,
            status=status,
            created_at=pay_date,
            updated_at=pay_date
        )
        
        if not is_success:
            # Pick a failure category
            # Weight transient errors higher
            cat_choice = random.choices(
                FAILURE_TYPES,
                weights=[0.30, 0.15, 0.10, 0.20, 0.10, 0.03, 0.05, 0.02, 0.03, 0.02]
            )[0]
            pay.failure_category = cat_choice[0]
            pay.failure_code = cat_choice[1]
            pay.failure_reason = cat_choice[2]
            
            # Let's say some of them have already been recovered previously to populate recovered metrics!
            # Out of failed ones, let's say 40% were recovered
            if random.random() < 0.40:
                # Set status to RECOVERED and add retry records
                pay.status = "RECOVERED"
                pay.retry_count = 1
                
                # We'll save it first to get an ID
                db.add(pay)
                db.commit()
                
                # Add decision
                dec = RecoveryDecision(
                    payment_id=pay.id,
                    decision="RETRY",
                    confidence=0.88,
                    explanation="Temporary bank failure identified. Highly recoverable. Initiating retry.",
                    policy_result="APPROVED",
                    created_at=pay_date + timedelta(minutes=5)
                )
                db.add(dec)
                
                # Add attempt
                att = RecoveryAttempt(
                    payment_id=pay.id,
                    attempt_number=1,
                    strategy="RETRY_AFTER_DELAY",
                    reason="Temporary bank failure retry.",
                    recovery_probability=0.88,
                    status="SUCCESS",
                    executed_at=pay_date + timedelta(minutes=20),
                    result='{"razorpay_payment_id": "pay_test_ret_seeded"}',
                    created_at=pay_date + timedelta(minutes=20)
                )
                db.add(att)
                
                # Add audit logs
                a1 = AuditLog(
                    payment_id=pay.id,
                    action="PAYMENT_FAILED",
                    actor="RAZORPAY_SERVICE",
                    reason=f"Initial payment failed: {pay.failure_reason}",
                    metadata_json=f'{{"error_code": "{pay.failure_code}"}}',
                    timestamp=pay_date
                )
                a2 = AuditLog(
                    payment_id=pay.id,
                    action="AI_DECISION_CREATED",
                    actor="AI_AGENT",
                    reason="AI analyzed failure and recommended RETRY with 88% probability.",
                    metadata_json='{"decision": "RETRY", "confidence": 0.88}',
                    timestamp=pay_date + timedelta(minutes=5)
                )
                a3 = AuditLog(
                    payment_id=pay.id,
                    action="POLICY_APPROVED",
                    actor="POLICY_ENGINE",
                    reason="Action approved by deterministic guards.",
                    metadata_json='{}',
                    timestamp=pay_date + timedelta(minutes=6)
                )
                a4 = AuditLog(
                    payment_id=pay.id,
                    action="RECOVERY_SUCCEEDED",
                    actor="RAZORPAY_SERVICE",
                    reason="Recovery succeeded on attempt #1. Revenue recovered.",
                    metadata_json='{"razorpay_payment_id": "pay_test_ret_seeded"}',
                    timestamp=pay_date + timedelta(minutes=20)
                )
                db.add_all([a1, a2, a3, a4])
                
            else:
                # Remains failed
                db.add(pay)
                db.commit()
                # Audit log for failure
                a1 = AuditLog(
                    payment_id=pay.id,
                    action="PAYMENT_FAILED",
                    actor="RAZORPAY_SERVICE",
                    reason=f"Initial payment failed: {pay.failure_reason}",
                    metadata_json=f'{{"error_code": "{pay.failure_code}"}}',
                    timestamp=pay_date
                )
                db.add(a1)
        else:
            # Success payment
            db.add(pay)
            db.commit()
            
        payments_seeded += 1
        
    db.commit()
    print(f"Seeded {payments_seeded} payments successfully.")
    return merchant.id
