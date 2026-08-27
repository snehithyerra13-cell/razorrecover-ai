from app.config import settings

def validate_action(
    payment_status: str,
    failure_category: str,
    amount: float,
    retry_count: int,
    recovery_probability: float,
    ai_decision: str,
    ai_strategy: str
) -> tuple[bool, str]:
    """
    Validates recommended AI actions against deterministic safety guardrails.
    Returns: (is_approved, reason)
    """
    
    # Rule 1: Payment must be in FAILED status to recover
    if payment_status != "FAILED":
        return False, f"Action blocked: payment status is '{payment_status}', but recovery is only allowed for FAILED payments."

    # Rule 2: Validation of basic transaction integrity
    if amount <= 0:
        return False, "Action blocked: transaction amount must be greater than zero."

    # Rule 3: Enforce strict retry count limits
    if ai_decision == "RETRY" and retry_count >= settings.MAX_RETRIES:
        return False, f"Action blocked: maximum retry limit ({settings.MAX_RETRIES}) exceeded. Current retries: {retry_count}."

    # Rule 4: Expired card cannot be retried automatically
    if failure_category == "EXPIRED_CARD" and ai_decision == "RETRY":
        return False, "Action blocked: expired cards cannot be automatically retried. Requires payment credentials update."

    # Rule 5: Invalid card cannot be retried or recovered
    if failure_category == "INVALID_CARD" and ai_decision in ["RETRY", "NOTIFY_CUSTOMER"]:
        return False, "Action blocked: transaction has been flagged as an invalid card. Blocked for fraud protection."

    # Rule 6: Permanent failures cannot be recovered
    if failure_category == "PERMANENT_FAILURE" and ai_decision not in ["STOP", "NO_ACTION"]:
        return False, f"Action blocked: permanent failure category '{failure_category}' cannot be retried."

    # Rule 7: Prevent retrying very low probability recovery attempts to save costs
    if ai_decision == "RETRY" and recovery_probability < settings.MIN_RECOVERY_PROBABILITY:
        return False, (
            f"Action blocked: recovery probability ({recovery_probability:.0%}) is below "
            f"the safety threshold ({settings.MIN_RECOVERY_PROBABILITY:.0%})."
        )

    # Rule 8: Restrict allowed actions to safe predefined list
    allowed_decisions = ["RETRY", "NOTIFY_CUSTOMER", "REQUEST_PAYMENT_UPDATE", "ESCALATE", "STOP", "NO_ACTION"]
    if ai_decision not in allowed_decisions:
        return False, f"Action blocked: AI decision '{ai_decision}' is not in the list of allowed financial operations."

    return True, "Action approved by the deterministic Policy & Safety Engine."
