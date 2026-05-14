import re

from .utils import KeyGenerator, clean_text, first_present, parse_int, slug_key


ASSET_CLASSES = ["SITE", "BLOCK", "INVERTER", "MOD", "SCB", "STRING", "PV_MODULE", "METER", "WEATHER"]


def _block_sort(value):
    match = re.search(r"(\d+)", clean_text(value))
    return int(match.group(1)) if match else 99999


def _row_value(row, column_prefix):
    for col, value in row.items():
        if col == column_prefix or col.startswith(f"{column_prefix}_"):
            if clean_text(value):
                return value
    return ""


def generate_assets(workbook, party_id, site_ref_key):
    keygen = KeyGenerator()
    assets = []
    hierarchy = []
    equipment = []
    attributes = []
    seen_assets = set()

    def add_asset(asset_ref_key, asset_class_key, asset_name="", parent_key=None, source_ref="", is_container="Y"):
        if asset_ref_key not in seen_assets:
            seen_assets.add(asset_ref_key)
            assets.append(
                {
                    "party_id": party_id,
                    "asset_ref_key": asset_ref_key,
                    "asset_class_key": asset_class_key,
                    "asset_name": asset_name or asset_ref_key,
                    "source_ref": source_ref,
                    "upd_dt": "now()",
                    "upd_by": "SYSTEM",
                }
            )
        if parent_key:
            hierarchy.append(
                {
                    "party_id": party_id,
                    "asset_ref_key": asset_ref_key,
                    "parent_asset_ref_key": parent_key,
                    "upd_dt": "now()",
                    "upd_by": "SYSTEM",
                    "is_container": is_container,
                    "container_ref_key": parent_key,
                }
            )
        return asset_ref_key

    site_name = workbook.site_details.get("SITE_NAME") or workbook.site_details.get("CUSTOMER") or "Solar Site"
    add_asset(site_ref_key, "SITE", site_name, parent_key=party_id, source_ref=site_name)

    block_keys = {}
    inv_keys = {}
    mod_keys = {}

    inv_df = workbook.sheets.get("Inverter")
    if inv_df is not None:
        for block in sorted({clean_text(v) for v in inv_df.get("Block wise name", []) if clean_text(v)}, key=_block_sort):
            block_num = _block_sort(block)
            block_key = f"{site_ref_key}_BLK{block_num}" if block_num != 99999 else f"{site_ref_key}_{keygen.next('BLK')}"
            block_keys[block] = add_asset(block_key, "BLOCK", block, site_ref_key, block)

        for _, row in inv_df.iterrows():
            block_name = clean_text(row.get("Block wise name"))
            if not block_name:
                continue
            block_key = block_keys[block_name]
            mod_source = first_present(row, ["ITS--INV-M", "ITS-INV-M", "INV count"], "")
            inv_name = clean_text(row.get("Inverter Name")) or mod_source or keygen.next("INV")
            inv_base = re.sub(r"-M\d+$", "", clean_text(mod_source)) or slug_key(inv_name, keygen.next("INV"))
            inv_key = inv_keys.get(inv_base)
            if not inv_key:
                inv_key = f"{block_key}_{keygen.next('INV')}"
                inv_keys[inv_base] = add_asset(inv_key, "INVERTER", inv_name, block_key, inv_base)
                equipment.append(_equipment_row(party_id, site_ref_key, "Inverter", row))

            mod_key = f"{inv_key}_{keygen.next('MOD')}"
            mod_keys[clean_text(mod_source)] = add_asset(mod_key, "MOD", mod_source or mod_key, inv_key, mod_source)
            _append_attribute_rows(attributes, party_id, mod_key, row, ["Make", "Model", "Controller Ids", "Inverter Capacity AC (kW)", "Inverter DC Loading (kW) / MOD"])

            for col in [c for c in row.index if c == "SCB name" or c.startswith("SCB name_")]:
                scb_name = clean_text(row.get(col))
                if not scb_name:
                    continue
                suffix = col.replace("SCB name", "String/scb")
                string_count = parse_int(row.get(suffix), 0)
                scb_key = add_asset(f"{mod_key}_{keygen.next('SCB')}", "SCB", scb_name, mod_key, scb_name)
                for string_idx in range(1, string_count + 1):
                    add_asset(f"{scb_key}_STR{string_idx}", "STRING", f"{scb_name}-STRING-{string_idx}", scb_key, scb_name, "N")

    _add_pv_modules(workbook, party_id, site_ref_key, assets, hierarchy, attributes, add_asset, keygen)
    _add_meter_assets(workbook, party_id, site_ref_key, add_asset, equipment, keygen)
    _add_weather_assets(workbook, party_id, site_ref_key, add_asset, equipment, keygen)

    return {
        "assets": assets,
        "hierarchy": hierarchy,
        "equipment": equipment,
        "asset_attributes": attributes,
    }


def _equipment_row(party_id, site_ref_key, equip_name, row=None):
    if row is None:
        row = {}
    return {
        "party_id": party_id,
        "site_id": site_ref_key,
        "equip_name": equip_name,
        "equip_short_name": equip_name,
        "equip_make": clean_text(row.get("Make", "")),
        "equip_model": clean_text(row.get("Model", "")),
        "equip_serial_num": "",
        "supplier_oem_id": "",
        "status": "ACT",
        "created_by": "SYSTEM",
        "created_ts": "now()",
    }


def _append_attribute_rows(rows, party_id, asset_ref_key, source_row, columns):
    for column in columns:
        value = clean_text(source_row.get(column, ""))
        if value:
            rows.append(
                {
                    "party_id": party_id,
                    "asset_ref_key": asset_ref_key,
                    "attr_key": slug_key(column),
                    "attr_value": value,
                    "upd_dt": "now()",
                    "upd_by": "SYSTEM",
                }
            )


def _add_pv_modules(workbook, party_id, site_ref_key, assets, hierarchy, attributes, add_asset, keygen):
    pv_df = workbook.sheets.get("PVModules")
    if pv_df is None:
        return
    total_panel_area = 0.0
    for _, row in pv_df.iterrows():
        name = clean_text(row.get("PV Module Name"))
        if not name:
            continue
        asset_ref_key = add_asset(f"{site_ref_key}_{keygen.next('PV')}", "PV_MODULE", name, site_ref_key, name, "N")
        _append_attribute_rows(
            attributes,
            party_id,
            asset_ref_key,
            row,
            ["No. of Panels", "Rating", "Pv panel make", "Panel Type", "PV Panel efficiency", "Panel Size(Sq. meter)", "Total Panel Area"],
        )
        try:
            total_panel_area += float(row.get("Total Panel Area") or 0)
        except (TypeError, ValueError):
            pass
    if total_panel_area:
        attributes.append(
            {
                "party_id": party_id,
                "asset_ref_key": site_ref_key,
                "attr_key": "TOTAL_PANEL_AREA",
                "attr_value": round(total_panel_area, 3),
                "upd_dt": "now()",
                "upd_by": "SYSTEM",
            }
        )


def _add_meter_assets(workbook, party_id, site_ref_key, add_asset, equipment, keygen):
    meter_df = workbook.sheets.get("Meter")
    if meter_df is None:
        return
    for _, row in meter_df.iterrows():
        name = clean_text(_row_value(row, "Meter Type")) or clean_text(row.get("Meter Type"))
        if not name:
            continue
        add_asset(f"{site_ref_key}_{keygen.next('MTR')}", "METER", name, site_ref_key, name, "N")
        equipment.append(_equipment_row(party_id, site_ref_key, name, row))


def _add_weather_assets(workbook, party_id, site_ref_key, add_asset, equipment, keygen):
    weather_df = workbook.sheets.get("Weather")
    if weather_df is None:
        return
    for _, row in weather_df.iterrows():
        device = clean_text(row.get("Device Name"))
        controller = clean_text(row.get("Controller ID"))
        if not device and not controller:
            continue
        name = f"{device} {controller}".strip()
        add_asset(f"{site_ref_key}_{keygen.next('WMS')}", "WEATHER", name, site_ref_key, controller, "N")
        equipment.append(_equipment_row(party_id, site_ref_key, "Weather Station", row))
