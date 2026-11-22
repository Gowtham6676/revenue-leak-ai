"""STEPS 2-4 - the AGENTS. Each agent has ONE job (like a team in a company).
  StrategistAgent : decides WHAT action to take for a leak   (agentic reasoning)
  WriterAgent     : writes the customer message              (generative AI)
  GuardrailAgent  : decides if a human must approve          (safety / governance)
Every agent has a rule-based fallback, so the system works even without Ollama."""
import llm
from config import COMPANY_NAME, SENDER_NAME, APPROVAL_THRESHOLD

ACTIONS = {
    "send_payment_reminder": "Polite reminder with payment link for overdue invoices.",
    "retry_payment": "Retry the failed card charge and notify the customer.",
    "issue_corrected_invoice": "Create a new invoice for usage/renewal that was never billed.",
    "send_retention_offer": "Reach out with help/discount to an at-risk customer.",
    "escalate_to_human": "Too complex or risky; hand to a finance manager.",
}
DEFAULT_ACTION = {
    "overdue_invoice": "send_payment_reminder",
    "failed_payment": "retry_payment",
    "unbilled_overage": "issue_corrected_invoice",
    "missed_renewal": "issue_corrected_invoice",
    "churn_risk": "send_retention_offer",
}


class StrategistAgent:
    system = ("You are a revenue-recovery strategist for a SaaS company. Choose the single best action "
              "for the leak. Reply ONLY as JSON: {\"action\": <one of the allowed actions>, "
              "\"tone\": \"friendly|firm|urgent\", \"reason\": \"one short sentence\"}")

    def decide(self, leak):
        prompt = (f"Leak: {leak['type']} | customer: {leak['customer_name']} | amount: {leak['amount']} | "
                  f"details: {leak['details']}\nAllowed actions: {ACTIONS}")
        out = llm.ask(prompt, self.system, as_json=True)
        if isinstance(out, dict) and out.get("action") in ACTIONS:        # validate LLM output!
            return {"action": out["action"], "tone": out.get("tone", "friendly"),
                    "reason": out.get("reason", ""), "source": "llm"}
        tone = "firm" if leak["days"] > 30 else "friendly"
        return {"action": DEFAULT_ACTION[leak["type"]], "tone": tone,
                "reason": "Rule-based default.", "source": "rules"}


class WriterAgent:
    system = (f"You write short, professional, empathetic billing emails for {COMPANY_NAME}. "
              f"Sign as '{SENDER_NAME}'. Max 110 words. Never threaten. Return email body only.")

    def write(self, leak, decision):
        prompt = (f"Write an email to {leak['customer_name']}.\nSituation: {leak['details']}\n"
                  f"Amount: INR {leak['amount']}\nAction: {decision['action']}\nTone: {decision['tone']}")
        text = llm.ask(prompt, self.system)
        if text:
            return text, "llm"
        return self._template(leak, decision), "template"

    @staticmethod
    def _template(leak, decision):
        first = leak["customer_name"].split()[0]
        body = {
            "send_payment_reminder": f"We noticed an outstanding balance of INR {leak['amount']}. {leak['details']} You can settle it from your billing page.",
            "retry_payment": f"Your recent payment of INR {leak['amount']} didn't go through. We'll retry shortly - please make sure your card details are up to date.",
            "issue_corrected_invoice": f"During a billing review we found a pending charge of INR {leak['amount']}. {leak['details']} A corrected invoice is attached.",
            "send_retention_offer": "We noticed you've been using the product less lately. We'd love to help - reply to book a free 20-minute success call.",
            "escalate_to_human": "Our finance team will contact you shortly regarding your account.",
        }[decision["action"]]
        return f"Hi {first},\n\n{body}\n\nThank you,\n{SENDER_NAME}\n{COMPANY_NAME}"


class GuardrailAgent:
    def review(self, leak, decision):
        if decision["action"] == "escalate_to_human":
            return "needs_approval", "Strategist escalated."
        if leak["amount"] >= APPROVAL_THRESHOLD:
            return "needs_approval", f"Amount >= {APPROVAL_THRESHOLD}."
        if leak["type"] == "churn_risk":
            return "needs_approval", "Retention offers need account-manager sign-off."
        return "auto_approved", "Low risk."
