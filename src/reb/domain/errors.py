from __future__ import annotations


class RebError(Exception):
    """A typed, user-visible error. `code` is stable; `message` explains the remedy."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

    def to_dict(self) -> dict[str, str]:
        return {"error": self.code, "message": self.message}
