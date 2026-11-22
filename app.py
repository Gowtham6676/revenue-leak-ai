"""Dashboard:  streamlit run app.py   (run main.py first)"""
import pandas as pd
import streamlit as st
from config import OUT_DIR, OUTBOX_DIR

st.set_page_config(page_title="Revenue Leak AI", layout="wide")
st.title("Revenue Leak AI - Autonomous Recovery System")

try:
    df = pd.read_csv(OUT_DIR / "actions_log.csv")
except FileNotFoundError:
    st.error("Run `python main.py` first."); st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Leaks found", len(df))
c2.metric("Revenue at risk", f"INR {df.amount.sum():,.0f}")
c3.metric("Expected recovery", f"INR {df.expected_recovery.sum():,.0f}")
c4.metric("Need human approval", int((df.status == "needs_approval").sum()))

st.subheader("Leakage by type")
st.bar_chart(df.groupby("type").amount.sum())

st.subheader("Actions")
f = st.multiselect("Filter status", df.status.unique(), default=list(df.status.unique()))
st.dataframe(df[df.status.isin(f)][["leak_id", "customer_name", "type", "amount", "action", "status", "guardrail_reason"]],
             use_container_width=True)

st.subheader("Preview email")
pick = st.selectbox("Leak", df.leak_id)
st.code((OUTBOX_DIR / df[df.leak_id == pick].email_file.iloc[0]).read_text(encoding="utf-8"))
