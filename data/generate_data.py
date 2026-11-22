"""Creates a realistic fake SaaS company dataset with planted revenue leaks."""
import random
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_DIR

random.seed(42)
TODAY = pd.Timestamp.today().normalize()
PLANS = {"Starter": 999, "Pro": 4999, "Business": 14999}
INCLUDED = {"Starter": 1000, "Pro": 10000, "Business": 50000}
FIRST = ["Aarav", "Diya", "Rohan", "Meera", "Kabir", "Ananya", "Vikram", "Isha", "Arjun", "Sara"]
LAST = ["Nair", "Menon", "Iyer", "Sharma", "Patel", "Reddy", "Das", "Kumar", "Joseph", "Khan"]

customers, invoices, usage, subs = [], [], [], []
inv_no = 1000

for i in range(1, 61):
    cid = f"C{i:03d}"
    plan = random.choices(list(PLANS), weights=[5, 3, 2])[0]
    name = f"{random.choice(FIRST)} {random.choice(LAST)}"
    prev = random.randint(8, 40)
    # ~12% of customers quietly stop using the product (churn risk)
    last = int(prev * random.uniform(0.05, 0.3)) if random.random() < 0.12 else int(prev * random.uniform(0.8, 1.2))
    customers.append(dict(customer_id=cid, name=name, email=f"{name.split()[0].lower()}{i}@example.com",
                          plan=plan, monthly_price=PLANS[plan], account_status="active",
                          logins_prev_30=prev, logins_last_30=last))

    for m in (1, 2, 3):
        inv_no += 1
        issue = TODAY - pd.Timedelta(days=30 * m)
        roll = random.random()
        status = "paid"
        if m <= 2 and roll < 0.12:
            status = "unpaid"
        elif m <= 2 and roll < 0.20:
            status = "failed"
        invoices.append(dict(invoice_id=f"INV{inv_no}", customer_id=cid, amount=PLANS[plan],
                             issue_date=issue.date(), due_date=(issue + pd.Timedelta(days=15)).date(),
                             status=status, retry_count=0))

    used = int(INCLUDED[plan] * random.uniform(0.5, 1.0))
    if random.random() < 0.15:                      # overage that was never billed
        used = int(INCLUDED[plan] * random.uniform(1.1, 1.6))
    usage.append(dict(customer_id=cid, month=(TODAY - pd.Timedelta(days=30)).strftime("%Y-%m"),
                      units_used=used, units_included=INCLUDED[plan], overage_rate=1.5,
                      overage_billed=False))

    overdue_renewal = random.random() < 0.10        # renewal date passed, never renewed
    rdate = TODAY - pd.Timedelta(days=random.randint(3, 20)) if overdue_renewal else TODAY + pd.Timedelta(days=random.randint(10, 300))
    subs.append(dict(customer_id=cid, renewal_date=rdate.date(), renewed=not overdue_renewal, auto_renew=True))

DATA_DIR.mkdir(exist_ok=True)
pd.DataFrame(customers).to_csv(DATA_DIR / "customers.csv", index=False)
pd.DataFrame(invoices).to_csv(DATA_DIR / "invoices.csv", index=False)
pd.DataFrame(usage).to_csv(DATA_DIR / "usage.csv", index=False)
pd.DataFrame(subs).to_csv(DATA_DIR / "subscriptions.csv", index=False)
print(f"Generated data for {len(customers)} customers in {DATA_DIR}")
