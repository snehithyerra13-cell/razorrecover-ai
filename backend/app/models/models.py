import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from app.db.session import Base

def generate_uuid():
    return str(uuid.uuid4())

class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    customers = relationship("Customer", back_populates="merchant", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="merchant", cascade="all, delete-orphan")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False)
    customer_reference = Column(String, nullable=False, index=True) # e.g. cust_123
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    merchant = relationship("Merchant", back_populates="customers")
    payments = relationship("Payment", back_populates="customer", cascade="all, delete-orphan")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(String, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    
    # Razorpay Specifics
    razorpay_payment_id = Column(String, nullable=True, unique=True, index=True)
    
    amount = Column(Float, nullable=False) # In Rupees
    currency = Column(String, default="INR")
    payment_method = Column(String, nullable=False) # e.g. card, upi, netbanking, wallet
    status = Column(String, default="FAILED", index=True) # SUCCESS, FAILED, PENDING, RECOVERING, RECOVERED
    
    # Failures
    failure_code = Column(String, nullable=True)
    failure_reason = Column(String, nullable=True)
    failure_category = Column(String, nullable=True, index=True) # e.g. TEMPORARY_BANK_FAILURE, etc.
    
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    merchant = relationship("Merchant", back_populates="payments")
    customer = relationship("Customer", back_populates="payments")
    attempts = relationship("RecoveryAttempt", back_populates="payment", cascade="all, delete-orphan")
    decisions = relationship("RecoveryDecision", back_populates="payment", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="payment", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="payment", cascade="all, delete-orphan")


class RecoveryAttempt(Base):
    __tablename__ = "recovery_attempts"

    id = Column(String, primary_key=True, default=generate_uuid)
    payment_id = Column(String, ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    strategy = Column(String, nullable=False) # RETRY_AFTER_DELAY, CUSTOMER_NOTIFICATION, etc.
    reason = Column(Text, nullable=True)
    recovery_probability = Column(Float, nullable=False)
    status = Column(String, default="PENDING", index=True) # PENDING, SUCCESS, FAILED
    executed_at = Column(DateTime, default=datetime.utcnow)
    result = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    payment = relationship("Payment", back_populates="attempts")


class RecoveryDecision(Base):
    __tablename__ = "recovery_decisions"

    id = Column(String, primary_key=True, default=generate_uuid)
    payment_id = Column(String, ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    decision = Column(String, nullable=False) # RETRY, NOTIFY_CUSTOMER, STOP, etc.
    strategy = Column(String, nullable=True)
    confidence = Column(Float, nullable=False)
    explanation = Column(Text, nullable=False)
    policy_result = Column(String, nullable=False) # APPROVED, BLOCKED
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    payment = relationship("Payment", back_populates="decisions")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    payment_id = Column(String, ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    action = Column(String, nullable=False) # e.g. PAYMENT_FAILED, AI_DECISION_CREATED, etc.
    actor = Column(String, nullable=False) # AI_AGENT, POLICY_ENGINE, EXECUTOR, RAZORPAY_SERVICE
    reason = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True) # JSON stored as string
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    payment = relationship("Payment", back_populates="audit_logs")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=generate_uuid)
    payment_id = Column(String, ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    channel = Column(String, nullable=False) # EMAIL, SMS, WHATSAPP
    status = Column(String, default="PENDING") # PENDING, SENT, FAILED
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    payment = relationship("Payment", back_populates="notifications")
