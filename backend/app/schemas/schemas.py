from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional, Any

# --- Merchant ---
class MerchantBase(BaseModel):
    name: str
    email: str

class MerchantCreate(MerchantBase):
    pass

class MerchantResponse(MerchantBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Customer ---
class CustomerBase(BaseModel):
    customer_reference: str
    email: Optional[str] = None
    phone: Optional[str] = None

class CustomerCreate(CustomerBase):
    merchant_id: str

class CustomerResponse(CustomerBase):
    id: str
    merchant_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- RecoveryAttempt ---
class RecoveryAttemptBase(BaseModel):
    attempt_number: int
    strategy: str
    reason: Optional[str] = None
    recovery_probability: float
    status: str
    result: Optional[str] = None

class RecoveryAttemptResponse(RecoveryAttemptBase):
    id: str
    payment_id: str
    executed_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

# --- RecoveryDecision ---
class RecoveryDecisionBase(BaseModel):
    decision: str
    confidence: float
    explanation: str
    policy_result: str

class RecoveryDecisionResponse(RecoveryDecisionBase):
    id: str
    payment_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- AuditLog ---
class AuditLogBase(BaseModel):
    action: str
    actor: str
    reason: Optional[str] = None
    metadata_json: Optional[str] = None

class AuditLogResponse(AuditLogBase):
    id: str
    payment_id: str
    timestamp: datetime

    class Config:
        from_attributes = True

# --- Notification ---
class NotificationBase(BaseModel):
    channel: str
    status: str
    message: str

class NotificationResponse(NotificationBase):
    id: str
    payment_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Payment ---
class PaymentBase(BaseModel):
    amount: float
    currency: str = "INR"
    payment_method: str
    status: str
    failure_code: Optional[str] = None
    failure_reason: Optional[str] = None
    failure_category: Optional[str] = None
    retry_count: int

class PaymentCreate(BaseModel):
    customer_reference: str
    amount: float
    currency: str = "INR"
    payment_method: str
    failure_code: Optional[str] = None
    failure_reason: Optional[str] = None

class PaymentResponse(PaymentBase):
    id: str
    merchant_id: str
    customer_id: str
    razorpay_payment_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    customer: CustomerResponse
    attempts: List[RecoveryAttemptResponse] = []
    decisions: List[RecoveryDecisionResponse] = []

    class Config:
        from_attributes = True

# --- Analytics / Dashboard ---
class RecoveryRatePoint(BaseModel):
    date: str
    rate: float

class DashboardMetricsResponse(BaseModel):
    total_transactions: int
    successful_transactions: int
    failed_transactions: int
    recoverable_transactions: int
    recovery_attempts: int
    successful_recoveries: int
    recovery_rate: float # e.g. 62.4
    revenue_at_risk: float
    revenue_recovered: float
    revenue_remaining_at_risk: float
    average_recovery_time_minutes: float

# --- AI Analysis ---
class AnalysisResponse(BaseModel):
    payment_id: str
    failure_category: str
    recovery_probability: float
    ai_decision: str # RETRY, NOTIFY_CUSTOMER, STOP, etc.
    explanation: str
    policy_result: str # APPROVED, BLOCKED
    confidence: float

# --- Execute Recovery ---
class RecoveryResponse(BaseModel):
    payment_id: str
    success: bool
    status: str # SUCCESS, FAILED
    action_executed: str
    recovered_amount: float
    message: str
