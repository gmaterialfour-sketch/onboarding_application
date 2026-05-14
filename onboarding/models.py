from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class OnboardingJob(TimeStampedModel):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    original_filename = models.CharField(max_length=255)
    uploaded_file = models.FileField(upload_to="onboarding/uploads/")
    output_excel = models.FileField(upload_to="onboarding/outputs/", blank=True)
    output_sql = models.FileField(upload_to="onboarding/outputs/", blank=True)
    output_zip = models.FileField(upload_to="onboarding/outputs/", blank=True)
    party_id = models.CharField(max_length=64, default="SEKURA")
    site_ref_key = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default="PENDING")
    error_message = models.TextField(blank=True)
    summary = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.original_filename} ({self.status})"


class Party(TimeStampedModel):
    party_id = models.CharField(max_length=64, primary_key=True)
    party_name = models.CharField(max_length=255)
    status = models.CharField(max_length=24, default="ACT")
    upd_by = models.CharField(max_length=64, default="SYSTEM")

    def __str__(self):
        return self.party_id


class AssetClass(TimeStampedModel):
    party_id = models.CharField(max_length=64)
    asset_class_key = models.CharField(max_length=64)
    class_name = models.CharField(max_length=128)
    class_desc = models.TextField(blank=True)
    upd_by = models.CharField(max_length=64, default="SYSTEM")

    class Meta:
        unique_together = ("party_id", "asset_class_key")

    def __str__(self):
        return self.asset_class_key


class AssetMaster(TimeStampedModel):
    party_id = models.CharField(max_length=64)
    asset_ref_key = models.CharField(max_length=128)
    asset_class_key = models.CharField(max_length=64)
    asset_name = models.CharField(max_length=255, blank=True)
    source_ref = models.CharField(max_length=255, blank=True)
    upd_by = models.CharField(max_length=64, default="SYSTEM")

    class Meta:
        unique_together = ("party_id", "asset_ref_key")

    def __str__(self):
        return self.asset_ref_key


class AssetHierarchy(TimeStampedModel):
    party_id = models.CharField(max_length=64)
    asset_ref_key = models.CharField(max_length=128)
    parent_asset_ref_key = models.CharField(max_length=128)
    is_container = models.CharField(max_length=1, default="Y")
    container_ref_key = models.CharField(max_length=128)
    upd_by = models.CharField(max_length=64, default="SYSTEM")


class AssetClassAttributeMeasure(TimeStampedModel):
    party_id = models.CharField(max_length=64)
    asset_class_key = models.CharField(max_length=64)
    attr_ref_key = models.CharField(max_length=128)
    attr_name = models.CharField(max_length=255)
    data_type = models.CharField(max_length=32, default="NUMERIC")
    unit = models.CharField(max_length=32, blank=True)
    source = models.CharField(max_length=32, default="TEMPLATE")
    upd_by = models.CharField(max_length=64, default="SYSTEM")


class MqttMapping(TimeStampedModel):
    party_id = models.CharField(max_length=64)
    site_ref_key = models.CharField(max_length=128)
    asset_class_key = models.CharField(max_length=64)
    asset_ref_key = models.CharField(max_length=128)
    attr_ref_key = models.CharField(max_length=128)
    attr_data_type = models.CharField(max_length=32, default="NUMERIC")
    mqtt_topic = models.CharField(max_length=512)
    status = models.CharField(max_length=24, default="ACT")


class TelemetryMapping(TimeStampedModel):
    party_id = models.CharField(max_length=64)
    site_ref_key = models.CharField(max_length=128)
    asset_ref_key = models.CharField(max_length=128)
    asset_class_key = models.CharField(max_length=64)
    telemetry_key = models.CharField(max_length=128)
    source_tag = models.CharField(max_length=255)
    data_type = models.CharField(max_length=32, default="NUMERIC")
    unit = models.CharField(max_length=32, blank=True)
    status = models.CharField(max_length=24, default="ACT")


class Equipment(TimeStampedModel):
    party_id = models.CharField(max_length=64)
    site_id = models.CharField(max_length=128)
    equip_name = models.CharField(max_length=128)
    equip_short_name = models.CharField(max_length=128)
    equip_make = models.CharField(max_length=128, blank=True)
    equip_model = models.CharField(max_length=128, blank=True)
    equip_serial_num = models.CharField(max_length=128, blank=True)
    supplier_oem_id = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=24, default="ACT")
    created_by = models.CharField(max_length=64, default="SYSTEM")
