"""ORCHESTRATOR: runs the full loop  Detect -> Prioritize -> Decide -> Write -> Guardrail -> Act -> Report"""
import re
import pandas as pd
import llm
from config import OUT_DIR, OUTBOX_DIR, COMPANY_NAME
from detectors import detect_all
from agents import StrategistAgent, WriterAgent, GuardrailAgent


def run():
    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    for f in OUTBOX_DIR.glob("*.md"):
        f.unlink()
    print("Ollama available:", llm.ollama_available())

    leaks = detect_all()
    leaks.sort(key=lambda l: -l["expected_recovery"])                    # PRIORITIZE by money
    print(f"Detected {len(leaks)} leaks, total at risk INR {sum(l['amount'] for l in leaks):,.0f}")

    strategist, writer, guard = StrategistAgent(), WriterAgent(), GuardrailAgent()
    rows = []
    for leak in leaks:
        decision = strategist.decide(leak)
        email, email_src = writer.write(leak, decision)
        status, why = guard.review(leak, decision)
        path = OUTBOX_DIR / f"{leak['leak_id']}_{leak['customer_id']}.md"
        path.write_text(f"To: {leak['email']}\nStatus: {status} ({why})\n\n{email}\n", encoding="utf-8")
        rows.append({**leak, **decision, "status": status, "guardrail_reason": why,
                     "email_source": email_src, "email_file": path.name})
        print(f"  {leak['leak_id']} {leak['type']:<17} INR {leak['amount']:>9,.0f} -> {decision['action']} [{status}]")

    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "actions_log.csv", index=False)
    write_report(df)
    print(f"\nDone. See {OUT_DIR}/report.md, actions_log.csv and outbox/")


def write_report(df):
    total, expected = df.amount.sum(), df.expected_recovery.sum()
    by_type = df.groupby("type").agg(count=("leak_id", "count"), amount=("amount", "sum"),
                                     expected=("expected_recovery", "sum")).sort_values("amount", ascending=False)
    lines = [f"# Revenue Leak Report - {COMPANY_NAME}", "",
             f"- Leaks found: **{len(df)}**", f"- Revenue at risk: **INR {total:,.0f}**",
             f"- Expected recovery: **INR {expected:,.0f}**",
             f"- Auto-approved actions: **{(df.status == 'auto_approved').sum()}** | Needs human: **{(df.status == 'needs_approval').sum()}**",
             "", "## By leak type", "", "| Type | Count | Amount | Expected recovery |", "|---|---|---|---|"]
    for t, r in by_type.iterrows():
        lines.append(f"| {t} | {int(r['count'])} | {r['amount']:,.0f} | {r['expected']:,.0f} |")
    lines += ["", "## Top 10 opportunities", "", "| ID | Customer | Type | Amount | Action | Status |", "|---|---|---|---|---|---|"]
    for _, r in df.head(10).iterrows():
        lines.append(f"| {r.leak_id} | {r.customer_name} | {r.type} | {r.amount:,.0f} | {r.action} | {r.status} |")
    (OUT_DIR / "report.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    run()
