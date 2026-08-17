"""
Acme Dental customizations: weekend booking preference + emergency flag.
"""

CUSTOM_PROMPT_OVERRIDES = {
    "appointment_booking": "Offer Saturday morning slots first when possible.",
}

CUSTOM_RULES = [
    {"when": "message contains 'emergency' or 'pain'", "action": "escalate_human_urgent"},
    {"when": "message contains 'refund' or 'complaint'", "action": "escalate_human"},
]


def customize_agent(agent_name: str, input_data: dict) -> dict:
    if agent_name == "appointment_agent":
        input_data = {**input_data, "prefer_weekend": True}
    return input_data
