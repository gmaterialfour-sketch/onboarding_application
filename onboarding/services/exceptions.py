class OnboardingError(Exception):
    """Base exception for onboarding failures."""


class ValidationError(OnboardingError):
    """Raised when an uploaded workbook is structurally invalid."""

    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors or []
