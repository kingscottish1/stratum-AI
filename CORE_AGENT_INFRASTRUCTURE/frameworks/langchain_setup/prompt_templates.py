"""
Central prompt template registry.

Every prompt used by agency agents lives here (or is loaded from a
VERTICALS/<vertical>/templates/*.txt file). Keeping them in one place
makes versioning, A/B testing and review by non-engineers possible.
"""
from pathlib import Path

from langchain_core.prompts import PromptTemplate

_BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


def load_prompt_file(relative_path: str) -> str:
    """Load a raw prompt from a templates/*.txt file."""
    path = _BASE_DIR / relative_path
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


# --- Core shared templates ---------------------------------------------------
CLASSIFY_INTENT = PromptTemplate.from_template(
    """You are an intent classifier for a {vertical} AI agent.
Classify the following message into exactly one intent from this list:
{intents}

Message: {message}

Respond with only the intent id, nothing else."""
)

EXTRACT_ENTITIES = PromptTemplate.from_template(
    """Extract structured entities from the message below.
Schema: {schema}
Message: {message}
Return valid JSON matching the schema."""
)

GENERATE_REPLY = PromptTemplate.from_template(
    """You are {agent_name}, an AI assistant for {vertical}.
Tone: {tone}. Channel: {channel}.

Context:
{context}

Customer message:
{message}

Draft the reply now."""
)

# Registry so agents can look templates up by name
TEMPLATE_REGISTRY = {
    "classify_intent": CLASSIFY_INTENT,
    "extract_entities": EXTRACT_ENTITIES,
    "generate_reply": GENERATE_REPLY,
}


def get_template(name: str) -> PromptTemplate:
    if name not in TEMPLATE_REGISTRY:
        raise KeyError(f"Unknown prompt template: {name}")
    return TEMPLATE_REGISTRY[name]
