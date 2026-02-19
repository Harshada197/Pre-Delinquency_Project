"""
Equilibrate — Policy Engine v1.0
Loads policy_templates.json and provides recommended actions
based on hardship_type and risk_level.

No LLM. Rule-based only. Compliance-approved templates.

Usage:
    from policy_engine import get_recommended_action, get_policy_message
"""
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POLICY_PATH = os.path.join(BASE_DIR, "policy_templates.json")

_policy_cache = None


def _load_policies():
    global _policy_cache
    if _policy_cache is None:
        try:
            with open(POLICY_PATH, "r", encoding="utf-8") as f:
                _policy_cache = json.load(f)
        except Exception:
            _policy_cache = {}
    return _policy_cache


def get_recommended_action(hardship_type, risk_level):
    """Get the recommended action string for a hardship + risk combination.

    Returns a default string if no matching policy exists.
    """
    policies = _load_policies()
    hardship_key = hardship_type if hardship_type in policies else "NONE"
    policy = policies.get(hardship_key, {}).get(risk_level, {})
    return policy.get("action", "Continue standard monitoring")


def get_policy_message(hardship_type, risk_level, customer_id="", ref_id=""):
    """Get the full policy message template with variable substitution.

    Returns None if no message template exists for this combination.
    """
    policies = _load_policies()
    hardship_key = hardship_type if hardship_type in policies else "NONE"
    policy = policies.get(hardship_key, {}).get(risk_level, {})
    template = policy.get("message")

    if not template:
        return None

    message = template.replace("{customer_id}", str(customer_id))
    message = message.replace("{ref_id}", str(ref_id))
    return message


def get_priority(hardship_type, risk_level):
    """Get the priority level (URGENT/HIGH/MEDIUM/ROUTINE)."""
    policies = _load_policies()
    hardship_key = hardship_type if hardship_type in policies else "NONE"
    policy = policies.get(hardship_key, {}).get(risk_level, {})
    return policy.get("priority", "ROUTINE")


def get_sla_hours(hardship_type, risk_level):
    """Get the SLA hours for response."""
    policies = _load_policies()
    hardship_key = hardship_type if hardship_type in policies else "NONE"
    policy = policies.get(hardship_key, {}).get(risk_level, {})
    return policy.get("sla_hours", 168)
