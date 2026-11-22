"""STEP 1 - DETECT: plain pandas rules that find money the business is losing.
Each detector returns a list of 'leak' dicts. No AI needed here: rules are cheap,
fast and explainable. AI is used later where judgment/language is needed."""
import pandas as pd
from config import DATA_DIR

TODAY = pd.Timestamp.today().normalize()


def _load():
    d = {n: pd.read_csv(DATA_DIR / f"{n}.csv") for n in ("customers", "invoices", "usage", "subscriptions")}
    for col in ("issue_date", "due_date"):
        d["invoices"][col] = pd.to_datetime(d["invoices"][col])
    d["subscriptions"]["renewal_date"] = pd.to_datetime(d["subscriptions"]["renewal_date"])
    return d


def _leak(kind, row, amount, probability, details, days=0):
    return dict(type=kind, customer_id=row["customer_id"], customer_name=row["name"], email=row["email"],
                amount=round(float(amount), 2), probability=probability,
                expected_recovery=round(float(amount) * probability, 2), days=int(days), details=details)


def overdue_invoices(d):
    df = d["invoices"].merge(d["customers"], on="customer_id")
    df = df[(df.status == "unpaid") & (df.due_date < TODAY)]
    out = []
    for _, r in df.iterrows():
        late = (TODAY - r.due_date).days
        out.append(_leak("overdue_invoice", r, r.amount, max(0.2, 0.9 - late / 120),
                         f"Invoice {r.invoice_id} is {late} days overdue.", late))
    return out


def failed_payments(d):
    df = d["invoices"].merge(d["customers"], on="customer_id")
    df = df[(df.status == "failed") & (df.retry_count < 3)]
    return [_leak("failed_payment", r, r.amount, 0.8,
                  f"Card payment for {r.invoice_id} failed and was never retried.") for _, r in df.iterrows()]


def unbilled_overage(d):
    df = d["usage"].merge(d["customers"], on="customer_id")
    df = df[(df.units_used > df.units_included) & (~df.overage_billed)]
    return [_leak("unbilled_overage", r, (r.units_used - r.units_included) * r.overage_rate, 0.85,
                  f"Used {r.units_used - r.units_included} units above plan in {r.month}; never invoiced.")
            for _, r in df.iterrows()]


def missed_renewals(d):
    df = d["subscriptions"].merge(d["customers"], on="customer_id")
    df = df[(~df.renewed) & (df.renewal_date < TODAY) & (df.auto_renew)]
    return [_leak("missed_renewal", r, r.monthly_price * 12, 0.6,
                  f"Renewal was due {r.renewal_date.date()} but no new term/invoice exists.",
                  (TODAY - r.renewal_date).days) for _, r in df.iterrows()]


def churn_risk(d):
    df = d["customers"]
    df = df[(df.logins_prev_30 >= 8) & (df.logins_last_30 <= 0.4 * df.logins_prev_30)]
    return [_leak("churn_risk", r, r.monthly_price * 12, 0.4,
                  f"Logins fell from {r.logins_prev_30} to {r.logins_last_30} in 30 days.") for _, r in df.iterrows()]


def detect_all():
    d = _load()
    leaks = []
    for fn in (overdue_invoices, failed_payments, unbilled_overage, missed_renewals, churn_risk):
        leaks += fn(d)
    for i, l in enumerate(sorted(leaks, key=lambda x: -x["expected_recovery"]), 1):
        l["leak_id"] = f"L{i:03d}"
    return sorted(leaks, key=lambda x: x["leak_id"])
