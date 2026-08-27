import pytest
from app.policies.policy_engine import validate_action
from app.ml.predict import predict_recovery_probability

def test_policy_engine_rules():
    # Rule 1: payment status must be FAILED to recover
    approved, reason = validate_action(
        payment_status="SUCCESS",
        failure_category="TEMPORARY_BANK_FAILURE",
        amount=100.0,
        retry_count=0,
        recovery_probability=0.90,
        ai_decision="RETRY",
        ai_strategy="RETRY_AFTER_DELAY"
    )
    assert not approved
    assert "status is 'SUCCESS'" in reason

    # Rule 3: max retries limit (3)
    approved, reason = validate_action(
        payment_status="FAILED",
        failure_category="TEMPORARY_BANK_FAILURE",
        amount=100.0,
        retry_count=3,
        recovery_probability=0.90,
        ai_decision="RETRY",
        ai_strategy="RETRY_AFTER_DELAY"
    )
    assert not approved
    assert "maximum retry limit" in reason

    # Rule 4: expired card automatic retry blocked
    approved, reason = validate_action(
        payment_status="FAILED",
        failure_category="EXPIRED_CARD",
        amount=100.0,
        retry_count=0,
        recovery_probability=0.70,
        ai_decision="RETRY",
        ai_strategy="RETRY_AFTER_DELAY"
    )
    assert not approved
    assert "expired cards cannot be automatically retried" in reason

    # Rule 5: invalid card retry/notify blocked
    approved, reason = validate_action(
        payment_status="FAILED",
        failure_category="INVALID_CARD",
        amount=100.0,
        retry_count=0,
        recovery_probability=0.10,
        ai_decision="NOTIFY_CUSTOMER",
        ai_strategy="SMS_NOTIFICATION"
    )
    assert not approved
    assert "flagged as an invalid card" in reason

    # Rule 7: low probability retry blocked (< 50%)
    approved, reason = validate_action(
        payment_status="FAILED",
        failure_category="TEMPORARY_BANK_FAILURE",
        amount=100.0,
        retry_count=0,
        recovery_probability=0.35,
        ai_decision="RETRY",
        ai_strategy="RETRY_AFTER_DELAY"
    )
    assert not approved
    assert "recovery probability" in reason
    assert "below the safety threshold" in reason

    # Good transaction: APPROVED
    approved, reason = validate_action(
        payment_status="FAILED",
        failure_category="TEMPORARY_BANK_FAILURE",
        amount=500.0,
        retry_count=0,
        recovery_probability=0.85,
        ai_decision="RETRY",
        ai_strategy="RETRY_AFTER_DELAY"
    )
    assert approved
    assert "Action approved" in reason

def test_ml_prediction_fallback():
    prob = predict_recovery_probability(
        failure_category="TEMPORARY_BANK_FAILURE",
        payment_method="card",
        amount=500.0,
        retry_count=0,
        customer_success_rate=0.80
    )
    assert 0.0 <= prob <= 1.0
    assert prob > 0.60

    prob_low = predict_recovery_probability(
        failure_category="INVALID_CARD",
        payment_method="card",
        amount=15000.0,
        retry_count=2,
        customer_success_rate=0.10
    )
    assert prob_low <= 0.20
