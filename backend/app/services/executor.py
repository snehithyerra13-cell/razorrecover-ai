import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import Payment, RecoveryAttempt, RecoveryDecision, AuditLog, Notification, Customer
from app.services.razorpay_service import simulate_payment_retry, generate_simulated_payment_link

def log_audit_event(
    db: Session,
    payment_id: str,
    action: str,
    actor: str,
    reason: str,
    metadata_dict: dict = None
):
    """Immutable application-level audit logging helper."""
    meta_str = json.dumps(metadata_dict) if metadata_dict else "{}"
    audit_log = AuditLog(
        payment_id=payment_id,
        action=action,
        actor=actor,
        reason=reason,
        metadata_json=meta_str,
        timestamp=datetime.utcnow()
    )
    db.add(audit_log)
    db.commit()

def execute_recovery_action(
    db: Session,
    payment_id: str,
    decision_id: str
) -> dict:
    """
    Executes an approved recovery action for a payment.
    Enforces policy approval checks, updates payment status, and logs outcomes.
    """
    # 1. Fetch Payment and Decision
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    decision = db.query(RecoveryDecision).filter(RecoveryDecision.id == decision_id).first()

    if not payment:
        return {"success": False, "message": "Payment record not found."}
    if not decision:
        return {"success": False, "message": "Recovery decision not found."}
        
    # Check that decision was APPROVED by policy engine
    if decision.policy_result != "APPROVED":
        log_audit_event(
            db,
            payment_id=payment_id,
            action="EXECUTION_BLOCKED",
            actor="EXECUTOR",
            reason=f"Blocked: Action was not approved by policy engine. Decision: {decision.decision}.",
            metadata_dict={"decision": decision.decision, "policy_result": decision.policy_result}
        )
        return {"success": False, "message": f"Action blocked: Decision is {decision.policy_result}."}

    # Prevent duplicating executions
    existing_active_attempts = db.query(RecoveryAttempt).filter(
        RecoveryAttempt.payment_id == payment_id,
        RecoveryAttempt.status == "PENDING"
    ).first()
    if existing_active_attempts:
        return {"success": False, "message": "A recovery attempt is already active/pending for this payment."}

    action_type = decision.decision
    strategy = decision.strategy
    
    # Create the Recovery Attempt record
    attempt_num = payment.retry_count + 1 if action_type == "RETRY" else payment.retry_count
    attempt = RecoveryAttempt(
        payment_id=payment_id,
        attempt_number=attempt_num,
        strategy=strategy,
        reason=decision.explanation,
        recovery_probability=decision.confidence,
        status="PENDING",
        executed_at=datetime.utcnow()
    )
    db.add(attempt)
    db.commit()

    log_audit_event(
        db,
        payment_id=payment_id,
        action="RECOVERY_INITIATED",
        actor="EXECUTOR",
        reason=f"Initiated action: {action_type} using strategy: {strategy}.",
        metadata_dict={"strategy": strategy, "attempt_number": attempt_num}
    )

    customer = db.query(Customer).filter(Customer.id == payment.customer_id).first()
    customer_email = customer.email if customer else "customer@demo.com"
    customer_phone = customer.phone if customer else "+919876543210"

    success = False
    status_msg = "FAILED"
    result_meta = {}
    recovered_amount = 0.0

    if action_type == "RETRY":
        # Simulate network retry
        retry_res = simulate_payment_retry(payment.id, payment.failure_category)
        success = retry_res["success"]
        status_msg = "SUCCESS" if success else "FAILED"
        result_meta = {
            "razorpay_payment_id": retry_res["razorpay_payment_id"],
            "error_code": retry_res["error_code"],
            "error_reason": retry_res["error_reason"]
        }
        
        # Update attempt
        attempt.status = "SUCCESS" if success else "FAILED"
        attempt.result = json.dumps(result_meta)
        
        # Update payment
        payment.retry_count += 1
        if success:
            payment.status = "RECOVERED"
            payment.razorpay_payment_id = retry_res["razorpay_payment_id"]
            recovered_amount = payment.amount
            log_audit_event(
                db,
                payment_id=payment_id,
                action="RECOVERY_SUCCEEDED",
                actor="RAZORPAY_SERVICE",
                reason=f"Payment recovered successfully via retry. ID: {retry_res['razorpay_payment_id']}",
                metadata_dict=result_meta
            )
        else:
            payment.status = "FAILED"
            payment.failure_code = retry_res["error_code"]
            payment.failure_reason = retry_res["error_reason"]
            log_audit_event(
                db,
                payment_id=payment_id,
                action="RECOVERY_FAILED",
                actor="RAZORPAY_SERVICE",
                reason=f"Retry failed: {retry_res['error_reason']}",
                metadata_dict=result_meta
            )
            
    elif action_type in ["NOTIFY_CUSTOMER", "REQUEST_PAYMENT_UPDATE"]:
        # Simulate customer notification / update link
        paylink = generate_simulated_payment_link(payment.id, payment.amount)
        
        message_text = ""
        channel = "SMS"
        if action_type == "REQUEST_PAYMENT_UPDATE":
            channel = "EMAIL"
            message_text = f"Dear Customer, your payment of INR {payment.amount:.2f} failed due to expired card. Please update your payment credentials securely: {paylink}"
        else:
            # Insufficient funds or simple dropoff notification
            message_text = f"Dear Customer, your payment of INR {payment.amount:.2f} declined. Tap here to reload balance or select another payment option and complete checkout: {paylink}"

        # Create notification entry
        notif = Notification(
            payment_id=payment_id,
            channel=channel,
            status="SENT",
            message=message_text,
            created_at=datetime.utcnow()
        )
        db.add(notif)
        
        result_meta = {"channel": channel, "payment_link": paylink}
        attempt.status = "SUCCESS" # Sent successfully
        attempt.result = json.dumps(result_meta)
        
        # Update payment status to RECOVERING (waiting for customer interaction)
        payment.status = "RECOVERING"
        
        success = True
        status_msg = "SUCCESS"
        
        log_audit_event(
            db,
            payment_id=payment_id,
            action="CUSTOMER_NOTIFIED",
            actor="NOTIFICATION_SERVICE",
            reason=f"Sent recovery notification via {channel}.",
            metadata_dict=result_meta
        )
        
    elif action_type == "ESCALATE":
        result_meta = {"escalated_to": "Merchant Support Queue"}
        attempt.status = "SUCCESS"
        attempt.result = json.dumps(result_meta)
        payment.status = "FAILED" # Remains failed but flagged for escalation
        success = True
        status_msg = "SUCCESS"
        
        log_audit_event(
            db,
            payment_id=payment_id,
            action="RECOVERY_ESCALATED",
            actor="EXECUTOR",
            reason="Escalated high-value failure to manual support desk.",
            metadata_dict=result_meta
        )
        
    elif action_type == "STOP":
        result_meta = {"action": "STOPPED"}
        attempt.status = "SUCCESS"
        attempt.result = json.dumps(result_meta)
        payment.status = "FAILED"
        success = True
        status_msg = "SUCCESS"
        
        log_audit_event(
            db,
            payment_id=payment_id,
            action="RECOVERY_STOPPED",
            actor="POLICY_ENGINE",
            reason="Recovery efforts stopped per policy configuration.",
            metadata_dict=result_meta
        )
        
    db.commit()
    
    return {
        "success": success,
        "status": status_msg,
        "action_executed": action_type,
        "recovered_amount": recovered_amount,
        "message": f"Action '{action_type}' executed. Result status: {status_msg}."
    }
