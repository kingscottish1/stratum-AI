# Adding a New Agent (the Stratum way)

Adding an agent to any vertical takes an afternoon. Follow the pattern of
existing agents (e.g. `appointment_agent.py`).

## 1. Subclass BaseAgent
```python
from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.base_agent_class import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self, dep1, dep2, llm):
        super().__init__(name="my_agent", vertical="medical_dental_clinics", llm=llm)
        self.dep1 = dep1

    def run(self, input_data: dict) -> dict:
        # always return {"status": "success"|"error", "result": ..., "reply": ...}
        ...
```

## 2. Use tools through interfaces
Never call vendor SDKs directly inside an agent. Inject a connector that
implements the shared interface (`CRMInterface`, calendar contract, TMS
contract) — that's what makes the demos and tests possible.

## 3. Register it
- Add to the vertical's orchestrator (`agents` dict + routing branch).
- Add to `config.yaml` `agents.enabled` for the client instances.
- Add a workflow YAML in `VERTICALS/<vertical>/workflows/` describing
  triggers, steps, success criteria, fallback and metrics.

## 4. Templates
Put any user-facing wording in `VERTICALS/<vertical>/templates/` so the
client (and account manager) can review copy without touching code.

## 5. Test it
```python
# tests/test_my_agent.py
def test_my_agent_flow():
    agent = MyAgent(dep1=MockDep1(), dep2=MockDep2(), llm=None)
    result = agent.execute({...})
    assert result["status"] == "success"
```
Run `pytest tests/ -v`. Demos: add a scenario to `DEMOS/demo_<vertical>.py`.

## 6. Ship
- Update the vertical's `client_docs` (setup guide, FAQ).
- Update the landing page + pitch deck if the feature is sellable.
- CHANGELOG entry; CI runs lint + tests automatically.
