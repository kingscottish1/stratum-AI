"""
Build CrewAI crews from YAML configuration.

A crew is a reusable team of agents + tasks. Vertical orchestrators
assemble the right crew for a given workflow at runtime.
"""
from pathlib import Path
from typing import Optional

import yaml
from crewai import Agent, Crew, Task

CONFIG_DIR = Path(__file__).resolve().parent


def load_agents_config() -> dict:
    with open(CONFIG_DIR / "agents_config.yaml", "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_tasks_config() -> dict:
    with open(CONFIG_DIR / "tasks_config.yaml", "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def build_agent(spec: dict) -> Agent:
    return Agent(
        role=spec["role"],
        goal=spec["goal"],
        backstory=spec["backstory"],
        llm=spec.get("llm", "gpt-4o-mini"),
        allow_delegation=spec.get("allow_delegation", False),
        verbose=spec.get("verbose", False),
    )


def build_task(spec: dict, agents: dict[str, Agent]) -> Task:
    if spec["agent"] not in agents:
        raise KeyError(f"Unknown agent '{spec['agent']}' referenced by task '{spec['name']}'")
    return Task(
        description=spec["description"],
        expected_output=spec["expected_output"],
        agent=agents[spec["agent"]],
    )


def create_crew(agent_names: list[str], task_names: list[str], name: str = "generic") -> Crew:
    """Assemble a crew from the YAML config by agent/task names."""
    agents_cfg = load_agents_config()["agents"]
    tasks_cfg = load_tasks_config()["tasks"]

    agents = {a["name"]: build_agent(a) for a in agents_cfg if a["name"] in agent_names}
    tasks = [build_task(t, agents) for t in tasks_cfg if t["name"] in task_names]

    return Crew(
        agents=list(agents.values()),
        tasks=tasks,
        name=name,
        process="sequential",
        verbose=True,
    )
