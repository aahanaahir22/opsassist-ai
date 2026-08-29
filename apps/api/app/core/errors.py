from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class OpsAssistError(Exception):
    code: str
    message: str
    status_code: int = 400
    details: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message


class NotFoundError(OpsAssistError):
    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__("RESOURCE_NOT_FOUND", f"{resource} '{identifier}' was not found.", 404)


class PolicyError(OpsAssistError):
    pass
