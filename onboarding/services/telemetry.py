TELEMETRY_TEMPLATES = {
    "SITE": [
        ("ACTIVE_POWER", "kW"),
        ("TODAY_ENERGY", "kWh"),
        ("TOTAL_ENERGY", "MWh"),
        ("PR", "%"),
        ("CUF", "%"),
    ],
    "BLOCK": [
        ("ACTIVE_POWER", "kW"),
        ("TODAY_ENERGY", "kWh"),
    ],
    "INVERTER": [
        ("AC_POWER", "kW"),
        ("AC_CURRENT", "A"),
        ("AC_VOLTAGE", "V"),
        ("DC_POWER", "kW"),
        ("DC_CURRENT", "A"),
        ("DC_VOLTAGE", "V"),
        ("STATUS", ""),
    ],
    "MOD": [
        ("DC_POWER", "kW"),
        ("DC_CURRENT", "A"),
        ("DC_VOLTAGE", "V"),
    ],
    "SCB": [
        ("STRING_CURRENT", "A"),
        ("DC_CURRENT", "A"),
        ("DC_VOLTAGE", "V"),
    ],
    "STRING": [
        ("STRING_CURRENT", "A"),
    ],
    "METER": [
        ("ACTIVE_POWER", "kW"),
        ("EXPORT_ENERGY", "kWh"),
        ("IMPORT_ENERGY", "kWh"),
        ("FREQUENCY", "Hz"),
    ],
    "WEATHER": [
        ("GHI", "W/m2"),
        ("POA", "W/m2"),
        ("AMBIENT_TEMP", "C"),
        ("MODULE_TEMP", "C"),
        ("WIND_SPEED", "m/s"),
    ],
    "PV_MODULE": [
        ("PANEL_RATING", "W"),
        ("PANEL_COUNT", "count"),
    ],
}


def class_measure_rows(party_id):
    rows = []
    for asset_class, telemetry in TELEMETRY_TEMPLATES.items():
        for key, unit in telemetry:
            rows.append(
                {
                    "party_id": party_id,
                    "asset_class_key": asset_class,
                    "attr_ref_key": key,
                    "attr_name": key.replace("_", " ").title(),
                    "data_type": "NUMERIC" if key != "STATUS" else "TEXT",
                    "unit": unit,
                    "source": "TEMPLATE",
                    "upd_dt": "now()",
                    "upd_by": "SYSTEM",
                }
            )
    return rows


def telemetry_rows(party_id, site_ref_key, assets):
    rows = []
    for asset in assets:
        for key, unit in TELEMETRY_TEMPLATES.get(asset["asset_class_key"], []):
            rows.append(
                {
                    "party_id": party_id,
                    "site_ref_key": site_ref_key,
                    "asset_ref_key": asset["asset_ref_key"],
                    "asset_class_key": asset["asset_class_key"],
                    "telemetry_key": key,
                    "source_tag": f"{asset['asset_ref_key']}.{key}",
                    "data_type": "NUMERIC" if key != "STATUS" else "TEXT",
                    "unit": unit,
                    "status": "ACT",
                }
            )
    return rows
