"""Public hosted advisor declaration, separate from tool authorization."""
BETA = "advisor-tool-2026-03-01"


def advisor_tool(model, max_uses=1, max_tokens=2048):
    if not isinstance(model, str) or not model.strip():
        raise ValueError("a supported advisor model ID is required")
    if type(max_uses) is not int or max_uses < 1:
        raise ValueError("max_uses must be positive")
    if type(max_tokens) is not int or max_tokens < 1024:
        raise ValueError("max_tokens must be at least 1024")
    return {"type": "advisor_20260301", "name": "advisor", "model": model,
            "max_uses": max_uses, "max_tokens": max_tokens}
