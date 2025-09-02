from mlipx import __all__


def nodes() -> dict[str, list[str]]:
    """Return all available nodes."""
    return {"mlipx": __all__}
