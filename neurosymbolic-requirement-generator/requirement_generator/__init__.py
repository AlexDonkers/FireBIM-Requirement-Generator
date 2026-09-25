"""FireBIM Requirement Generator package."""

__all__ = ["RequirementGenerator"]


def __getattr__(name):
    if name == "RequirementGenerator":
        from .pipeline import RequirementGenerator
        return RequirementGenerator
    raise AttributeError(name)
