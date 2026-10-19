"""Expected domain failures for analysis input validation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ErrorDetail:
    code: str
    message: str
    field: str | None = None


class DomainInputError(ValueError):
    """An expected, user-correctable domain input failure."""

    def __init__(self, code: str, message: str, field: str | None = None) -> None:
        self.detail = ErrorDetail(code=code, message=message, field=field)
        super().__init__(message)

    def to_dict(self) -> dict[str, str | None]:
        return {
            "code": self.detail.code,
            "message": self.detail.message,
            "field": self.detail.field,
        }


class AnalysisInputError(DomainInputError):
    """An expected, user-correctable statistical analysis input failure."""
