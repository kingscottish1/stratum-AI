"""
Remax Denver customizations: office-level alert routing.
"""

CUSTOM_RULES = [
    {"when": "lead area == 'Highlands'", "action": "route_agent:jennifer"},
    {"when": "lead intent == 'sell' and timeline == 'asap'", "action": "priority_alert"},
]

AGENT_ROUTING = {
    "Highlands": "jennifer@remaxdenver.com",
    "Downtown": "marcus@remaxdenver.com",
    "default": "desk@remaxdenver.com",
}
