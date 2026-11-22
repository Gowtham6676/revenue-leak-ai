"""Central settings. Change these instead of hunting through code."""
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUT_DIR = BASE_DIR / "output"
OUTBOX_DIR = OUT_DIR / "outbox"

COMPANY_NAME = "CloudNest Software"      # the fictional business we are protecting
SENDER_NAME = "Billing Team"

OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"                # any model you pulled: qwen2.5, mistral, llama3.1...

# Guardrail: anything bigger than this needs a human to approve (real businesses do this!)
APPROVAL_THRESHOLD = 2000
