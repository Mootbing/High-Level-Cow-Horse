"""Agent registry — shared singleton for agent class registration."""

AGENT_REGISTRY: dict[str, type] = {}


def register_agent(agent_type: str):
    """Decorator to register an agent class."""
    def decorator(cls):
        AGENT_REGISTRY[agent_type] = cls
        cls.agent_type = agent_type
        return cls
    return decorator
