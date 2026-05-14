from .telemetry import TELEMETRY_TEMPLATES
from .utils import slug_key


def topic_for(site_ref_key, asset, telemetry_key):
    site = slug_key(site_ref_key).lower()
    asset_class = asset["asset_class_key"].lower()
    asset_key = slug_key(asset["asset_ref_key"]).lower()
    measure = telemetry_key.lower()
    return f"{site}/{asset_class}/{asset_key}/{measure}"


def mqtt_rows(party_id, site_ref_key, assets):
    rows = []
    for asset in assets:
        for telemetry_key, _unit in TELEMETRY_TEMPLATES.get(asset["asset_class_key"], []):
            rows.append(
                {
                    "party_id": party_id,
                    "site_ref_key": site_ref_key,
                    "asset_class_key": asset["asset_class_key"],
                    "asset_ref_key": asset["asset_ref_key"],
                    "attr_ref_key": telemetry_key,
                    "attr_data_type": "NUMERIC" if telemetry_key != "STATUS" else "TEXT",
                    "mqtt_topic": topic_for(site_ref_key, asset, telemetry_key),
                    "status": "ACT",
                    "update_ts": "now()",
                }
            )
    return rows
