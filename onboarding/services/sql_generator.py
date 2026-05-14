from .utils import sql_literal


TABLE_MAP = {
    "party": "ods.party",
    "asset_class": "ods.asset_class",
    "asset_master": "ods.asset_master",
    "asset_hierarchy": "ods.asset_hierarchy",
    "asset_class_attr_meas": "ods.asset_class_attr_meas",
    "asset_attr_master": "ods.asset_attr_master",
    "mqtt_mapping": "ods.mqtt_configuration",
    "equipment": "pds.equipment",
    "telemetry_mapping": "ods.telemetry_mapping",
}


SQL_ORDER = [
    "party",
    "asset_class",
    "asset_master",
    "asset_hierarchy",
    "asset_class_attr_meas",
    "asset_attr_master",
    "equipment",
    "telemetry_mapping",
    "mqtt_mapping",
]


def dataframe_inserts(sheet_name, df):
    table_name = TABLE_MAP[sheet_name]
    columns = list(df.columns)
    statements = []
    for _, row in df.iterrows():
        values = ", ".join(sql_literal(row[col]) for col in columns)
        column_sql = ", ".join(columns)
        statements.append(f"INSERT INTO {table_name} ({column_sql}) VALUES ({values});")
    return statements


def generate_sql(tables):
    lines = [
        "-- Solar onboarding SQL export",
        "-- PostgreSQL compatible insert script",
        "BEGIN;",
        "",
    ]
    for sheet_name in SQL_ORDER:
        df = tables.get(sheet_name)
        if df is None or df.empty:
            continue
        lines.append(f"-- {sheet_name}")
        lines.extend(dataframe_inserts(sheet_name, df))
        lines.append("")
    lines.append("COMMIT;")
    return "\n".join(lines)
