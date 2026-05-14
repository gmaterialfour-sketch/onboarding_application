from dataclasses import dataclass

from django.core.exceptions import ValidationError


@dataclass
class UploadPayload:
    file: object
    party_id: str = "SEKURA"
    site_ref_key: str = ""


class OnboardingUploadSerializer:
    """Small dependency-free serializer for upload endpoints."""

    allowed_extensions = {".xlsx", ".xlsm"}

    def __init__(self, files, data=None):
        self.files = files
        self.data = data or {}
        self.errors = {}
        self.validated_data = None

    def is_valid(self):
        upload = self.files.get("file") or self.files.get("real_data")
        if not upload:
            self.errors["file"] = "Upload an onboarding Excel file."
            return False
        filename = upload.name.lower()
        if not any(filename.endswith(ext) for ext in self.allowed_extensions):
            self.errors["file"] = "Only .xlsx and .xlsm files are supported."
            return False
        self.validated_data = UploadPayload(
            file=upload,
            party_id=(self.data.get("party_id") or "SEKURA").strip().upper(),
            site_ref_key=(self.data.get("site_ref_key") or "").strip().upper(),
        )
        return True

    def raise_exception(self):
        if self.errors:
            raise ValidationError(self.errors)
