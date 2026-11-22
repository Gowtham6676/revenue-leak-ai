# Revenue Leak AI - Autonomous Revenue Recovery System

Multi-agent system (Python + Ollama) that finds money a SaaS business is silently losing and
runs the recovery workflow with human-in-the-loop guardrails.

## Run
```
python -m venv venv && venv\Scripts\activate      # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
ollama pull llama3.2 && ollama serve              # optional; works without it (rule fallback)
python data/generate_data.py
python main.py
streamlit run app.py
```

## Architecture
Detect (pandas rules) -> Prioritize (expected value) -> Strategist agent (LLM, JSON) ->
Writer agent (LLM) -> Guardrail agent (policy) -> Act (outbox) -> Report/Dashboard
