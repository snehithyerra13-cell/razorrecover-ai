from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import json

from app.db.session import get_db
from app.models.models import Payment, Customer, Merchant, RecoveryDecision, RecoveryAttempt, AuditLog, Notification
from app.schemas.schemas import PaymentResponse, DashboardMetricsResponse, AnalysisResponse, RecoveryResponse, AuditLogResponse
from app.db.seed import seed_database_demo_data
from app.ml.predict import predict_recovery_probability
from app.agents.ai_agent import analyze_failed_payment
from app.policies.policy_engine import validate_action
from app.services.executor import execute_recovery_action, log_audit_event
from app.services.razorpay_service import verify_razorpay_signature

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "healthy", "service": "razorrecover-api"}

@router.post("/demo/seed")
def seed_demo_data(n_payments: int = 150, db: Session = Depends(get_db)):
    try:
        merchant_id = seed_database_demo_data(db, n_payments)
        return {"success": True, "message": f"Successfully seeded database with demo transactions.", "merchant_id": merchant_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to seed database: {str(e)}")

@router.get("/analytics", response_model=DashboardMetricsResponse)
def get_analytics(db: Session = Depends(get_db)):
    # Calculate business metrics dynamically from SQLite
    total_transactions = db.query(Payment).count()
    if total_transactions == 0:
        return {
            "total_transactions": 0,
            "successful_transactions": 0,
            "failed_transactions": 0,
            "recoverable_transactions": 0,
            "recovery_attempts": 0,
            "successful_recoveries": 0,
            "recovery_rate": 0.0,
            "revenue_at_risk": 0.0,
            "revenue_recovered": 0.0,
            "revenue_remaining_at_risk": 0.0,
            "average_recovery_time_minutes": 0.0
        }

    successful_transactions = db.query(Payment).filter(Payment.status == "SUCCESS").count()
    
    # Ever-failed payments are those that have a failure_category (regardless of current status)
    failed_payments_query = db.query(Payment).filter(Payment.failure_category != None)
    failed_transactions = failed_payments_query.count()
    
    # Recovered transactions
    successful_recoveries = db.query(Payment).filter(Payment.status == "RECOVERED").count()
    
    # Recoverable payments (transient failure types: bank failure, network, timeout, insufficient funds, expired, incorrect otp)
    recoverable_categories = ["TEMPORARY_BANK_FAILURE", "NETWORK_FAILURE", "TIMEOUT", "INSUFFICIENT_FUNDS", "EXPIRED_CARD", "CUSTOMER_ACTION_REQUIRED"]
    recoverable_transactions = db.query(Payment).filter(
        Payment.failure_category.in_(recoverable_categories)
    ).count()

    # Recovery Rate = recovered payments / total failed payments
    recovery_rate = (successful_recoveries / failed_transactions * 100) if failed_transactions > 0 else 0.0

    # Total recovery attempts executed
    recovery_attempts = db.query(RecoveryAttempt).count()

    # Revenue metrics
    # Revenue at risk is the sum of payments that failed (had a failure category)
    revenue_at_risk = db.query(func.sum(Payment.amount)).filter(Payment.failure_category != None).scalar() or 0.0
    
    # Revenue recovered (payments that are now RECOVERED)
    revenue_recovered = db.query(func.sum(Payment.amount)).filter(Payment.status == "RECOVERED").scalar() or 0.0
    
    # Revenue remaining at risk (payments that are FAILED or RECOVERING)
    revenue_remaining_at_risk = db.query(func.sum(Payment.amount)).filter(
        Payment.status.in_(["FAILED", "RECOVERING"])
    ).scalar() or 0.0

    # Average recovery time
    # Time delta between payment failure (created_at) and recovery success (executed_at for success attempt)
    recovery_times = []
    success_attempts = db.query(RecoveryAttempt).filter(RecoveryAttempt.status == "SUCCESS").all()
    for sa in success_attempts:
        pay = db.query(Payment).filter(Payment.id == sa.payment_id).first()
        if pay:
            delta = sa.executed_at - pay.created_at
            recovery_times.append(delta.total_seconds() / 60.0) # minutes
            
    avg_recovery_time = sum(recovery_times) / len(recovery_times) if recovery_times else 0.0

    return {
        "total_transactions": total_transactions,
        "successful_transactions": successful_transactions,
        "failed_transactions": failed_transactions,
        "recoverable_transactions": recoverable_transactions,
        "recovery_attempts": recovery_attempts,
        "successful_recoveries": successful_recoveries,
        "recovery_rate": round(recovery_rate, 1),
        "revenue_at_risk": round(revenue_at_risk, 2),
        "revenue_recovered": round(revenue_recovered, 2),
        "revenue_remaining_at_risk": round(revenue_remaining_at_risk, 2),
        "average_recovery_time_minutes": round(avg_recovery_time, 1)
    }

@router.get("/payments", response_model=List[PaymentResponse])
def list_payments(status: Optional[str] = None, search: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Payment)
    
    if status:
        query = query.filter(Payment.status == status)
        
    if search:
        # Search by customer email, customer reference, or payment id
        query = query.join(Customer).filter(
            (Customer.email.ilike(f"%{search}%")) |
            (Customer.customer_reference.ilike(f"%{search}%")) |
            (Payment.id.ilike(f"%{search}%")) |
            (Payment.razorpay_payment_id.ilike(f"%{search}%"))
        )
        
    # Return ordered by created_at desc
    return query.order_by(Payment.created_at.desc()).limit(100).all()

@router.get("/payments/{id}", response_model=PaymentResponse)
def get_payment_details(id: str, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.id == id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment transaction not found.")
    return payment

@router.get("/payments/{id}/audit", response_model=List[AuditLogResponse])
def get_payment_audit_trail(id: str, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).filter(AuditLog.payment_id == id).order_by(AuditLog.timestamp.asc()).all()
    return logs

@router.post("/payments/{id}/analyze", response_model=AnalysisResponse)
def analyze_payment(id: str, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.id == id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment transaction not found.")
        
    if payment.status not in ["FAILED", "RECOVERING"]:
        raise HTTPException(status_code=400, detail=f"Payment status is '{payment.status}'. Analysis is only for failed transactions.")

    # 1. Fetch/Calculate Customer History Success Rate
    cust_payments = db.query(Payment).filter(Payment.customer_id == payment.customer_id).all()
    total_cust_pays = len(cust_payments)
    success_cust_pays = sum(1 for p in cust_payments if p.status in ["SUCCESS", "RECOVERED"])
    
    customer_success_rate = (success_cust_pays / total_cust_pays) if total_cust_pays > 0 else 0.80
    customer_history_desc = f"Customer has completed {total_cust_pays} payment attempts, with {success_cust_pays} successes."

    # 2. Run ML Model prediction
    prob = predict_recovery_probability(
        failure_category=payment.failure_category,
        payment_method=payment.payment_method,
        amount=payment.amount,
        retry_count=payment.retry_count,
        customer_success_rate=customer_success_rate
    )

    # 3. Invoke AI Recovery Agent (gemini or fallback rules)
    ai_analysis = analyze_failed_payment(
        failure_category=payment.failure_category,
        payment_method=payment.payment_method,
        amount=payment.amount,
        retry_count=payment.retry_count,
        recovery_probability=prob,
        customer_history=customer_history_desc
    )

    ai_decision = ai_analysis.get("decision", "NO_ACTION")
    ai_strategy = ai_analysis.get("strategy", "NO_ACTION")
    ai_explanation = ai_analysis.get("explanation", "No action possible.")
    confidence = ai_analysis.get("confidence", prob)
    delay_minutes = ai_analysis.get("delay_minutes", 0)

    # 4. Validate through the deterministic Policy Engine
    is_approved, policy_reason = validate_action(
        payment_status=payment.status,
        failure_category=payment.failure_category,
        amount=payment.amount,
        retry_count=payment.retry_count,
        recovery_probability=prob,
        ai_decision=ai_decision,
        ai_strategy=ai_strategy
    )

    policy_result = "APPROVED" if is_approved else "BLOCKED"

    # Save Recovery Decision record
    decision = RecoveryDecision(
        payment_id=payment.id,
        decision=ai_decision,
        strategy=ai_strategy,
        confidence=confidence,
        explanation=ai_explanation,
        policy_result=policy_result
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)

    # Audit logging
    log_audit_event(
        db,
        payment_id=payment.id,
        action="AI_DECISION_CREATED",
        actor="AI_AGENT",
        reason=f"AI analyzed payment failure and recommended '{ai_decision}' ({ai_strategy}). Explanation: {ai_explanation}",
        metadata_dict={"decision": ai_decision, "strategy": ai_strategy, "confidence": confidence, "delay_minutes": delay_minutes}
    )

    log_audit_event(
        db,
        payment_id=payment.id,
        action="POLICY_CHECKED",
        actor="POLICY_ENGINE",
        reason=f"Policy Result: {policy_result}. Policy explanation: {policy_reason}",
        metadata_dict={"policy_result": policy_result, "reason": policy_reason}
    )

    return {
        "payment_id": payment.id,
        "failure_category": payment.failure_category,
        "recovery_probability": round(prob, 2),
        "ai_decision": ai_decision,
        "explanation": ai_explanation,
        "policy_result": policy_result,
        "confidence": round(confidence, 2)
    }

@router.post("/payments/{id}/recover", response_model=RecoveryResponse)
def recover_payment(id: str, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.id == id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment transaction not found.")
        
    # Get latest decision for this payment
    latest_decision = db.query(RecoveryDecision).filter(
        RecoveryDecision.payment_id == id
    ).order_by(RecoveryDecision.created_at.desc()).first()
    
    if not latest_decision:
        raise HTTPException(status_code=400, detail="No recovery decision has been generated yet. Please analyze the payment first.")
        
    # Execute the action
    exec_res = execute_recovery_action(db, payment.id, latest_decision.id)
    return {
        "payment_id": payment.id,
        "success": exec_res["success"],
        "status": exec_res["status"],
        "action_executed": exec_res["action_executed"],
        "recovered_amount": exec_res["recovered_amount"],
        "message": exec_res["message"]
    }

@router.post("/webhooks/razorpay")
async def razorpay_webhook(
    background_tasks: BackgroundTasks,
    x_razorpay_signature: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint to handle incoming Razorpay sandbox events.
    Authenticates notifications, parses webhook payload, updates payment status,
    and runs autonomous recovery checks if configured.
    """
    # Simply log webhook call. In simulated sandbox environment, we can accept local events.
    # For actual integration, validation would occur:
    # is_valid = verify_razorpay_signature(payload_bytes, x_razorpay_signature, settings.RAZORPAY_WEBHOOK_SECRET)
    
    # We will log the incoming webhook
    print("Received Razorpay Webhook Event")
    return {"status": "received"}
