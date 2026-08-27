export interface Merchant {
  id: string;
  name: string;
  email: string;
  created_at: string;
}

export interface Customer {
  id: string;
  merchant_id: string;
  customer_reference: string;
  email: string | null;
  phone: string | null;
  created_at: string;
}

export interface RecoveryAttempt {
  id: string;
  payment_id: string;
  attempt_number: number;
  strategy: string;
  reason: string | null;
  recovery_probability: number;
  status: 'PENDING' | 'SUCCESS' | 'FAILED';
  executed_at: string;
  result: string | null; // JSON String
  created_at: string;
}

export interface RecoveryDecision {
  id: string;
  payment_id: string;
  decision: 'RETRY' | 'NOTIFY_CUSTOMER' | 'REQUEST_PAYMENT_UPDATE' | 'ESCALATE' | 'STOP' | 'NO_ACTION';
  confidence: number;
  explanation: string;
  policy_result: 'APPROVED' | 'BLOCKED';
  created_at: string;
}

export interface AuditLog {
  id: string;
  payment_id: string;
  action: string;
  actor: 'AI_AGENT' | 'POLICY_ENGINE' | 'EXECUTOR' | 'RAZORPAY_SERVICE' | 'NOTIFICATION_SERVICE';
  reason: string | null;
  metadata_json: string | null; // JSON String
  timestamp: string;
}

export interface Notification {
  id: string;
  payment_id: string;
  channel: 'EMAIL' | 'SMS' | 'WHATSAPP';
  status: string;
  message: string;
  created_at: string;
}

export interface Payment {
  id: string;
  merchant_id: string;
  customer_id: string;
  razorpay_payment_id: string | null;
  amount: number;
  currency: string;
  payment_method: string;
  status: 'SUCCESS' | 'FAILED' | 'PENDING' | 'RECOVERING' | 'RECOVERED';
  failure_code: string | null;
  failure_reason: string | null;
  failure_category: string | null;
  retry_count: number;
  created_at: string;
  updated_at: string;
  customer: Customer;
  attempts: RecoveryAttempt[];
  decisions: RecoveryDecision[];
}

export interface DashboardMetrics {
  total_transactions: number;
  successful_transactions: number;
  failed_transactions: number;
  recoverable_transactions: number;
  recovery_attempts: number;
  successful_recoveries: number;
  recovery_rate: number;
  revenue_at_risk: number;
  revenue_recovered: number;
  revenue_remaining_at_risk: number;
  average_recovery_time_minutes: number;
}

export interface AnalysisResponse {
  payment_id: string;
  failure_category: string;
  recovery_probability: number;
  ai_decision: string;
  explanation: string;
  policy_result: 'APPROVED' | 'BLOCKED';
  confidence: number;
}

export interface RecoveryResponse {
  payment_id: string;
  success: boolean;
  status: string;
  action_executed: string;
  recovered_amount: number;
  message: string;
}
