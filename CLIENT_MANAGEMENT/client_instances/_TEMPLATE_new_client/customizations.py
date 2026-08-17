"""
Per-client customizations.

Anything vertical-specific that doesn't belong in shared code goes here.
The orchestrator loads this module at startup if it exists.
"""

CUSTOM_PROMPT_OVERRIDES = {}
# e.g.:
# CUSTOM_PROMPT_OVERRIDES = {
#     "appointment_booking": "always offer Saturday slots first",
# }

CUSTOM_RULES = []
# e.g.:
# CUSTOM_RULES = [
#     {"when": "message contains 'emergency'", "action": "escalate_human"},
# ]


def customize_agent(agent_name: str, input_data: dict) -> dict:
    """Hook: mutate input_data before the agent runs. Return unchanged by default."""
    return input_data


def post_process(agent_name: str, result: dict) -> dict:
    """Hook: adjust the agent result before it's sent. Return unchanged by default."""
    return result
