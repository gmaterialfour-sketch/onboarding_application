import re

import pandas as pd

from .hierarchy import ASSET_CLASSES, generate_assets
from .mqtt import mqtt_rows
from .telemetry import class_measure_rows, telemetry_rows
from .utils import clean_text, slug_key


def derive_site_ref_key(workbook):
    site_name = workbook.site_details.get("SITE_NAME") or workbook.site_details.get("CUSTOMER") or "SITE"
    text = clean_text(site_name).upper()
    if "BEEMPOW" in text or "BEPL" in text:
        return "BEPL_SITE001"
    acronym = "".join(word[0] for word in re.findall(r"[A-Z0-9]+", text)[:3]) or "SITE"
    return f"{slug_key(acronym, 'SITE')}_SITE001"


def build_normalized_tables(workbook, party_id="SEKURA", site_ref_key=None):
    site_ref_key = site_ref_key or derive_site_ref_key(workbook)
    generated = generate_assets(workbook, party_id, site_ref_key)
    assets = generated["assets"]

    tables = {
        "party": [
            {
                "party_id": party_id,
                "party_name": party_id,
                "upd_dt": "now()",
                "upd_by": "SYSTEM",
                "status": "ACT",
            }
        ],
        "asset_class": [
            {
                "party_id": party_id,
                "asset_class_key": asset_class,
                "class_name": asset_class,
                "class_desc": asset_class.replace("_", " ").title(),
                "upd_dt": "now()",
                "upd_by": "SYSTEM",
            }
            for asset_class in ASSET_CLASSES
        ],
        "asset_master": assets,
        "asset_hierarchy": generated["hierarchy"],
        "asset_class_attr_meas": class_measure_rows(party_id),
        "asset_attr_master": generated["asset_attributes"],
        "mqtt_mapping": mqtt_rows(party_id, site_ref_key, assets),
        "equipment": _dedupe_equipment(generated["equipment"]),
        "telemetry_mapping": telemetry_rows(party_id, site_ref_key, assets),
    }
    return {name: pd.DataFrame(rows) for name, rows in tables.items()}


def _dedupe_equipment(rows):
    seen = set()
    output = []
    for row in rows:
        key = (row["site_id"], row["equip_name"], row.get("equip_make", ""), row.get("equip_model", ""))
        if key in seen:
            continue
        seen.add(key)
        output.append(row)
    return output
