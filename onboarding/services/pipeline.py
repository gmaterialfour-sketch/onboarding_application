import logging
from pathlib import Path
from uuid import uuid4

from django.conf import settings

from .exceptions import ValidationError
from .exporter import export_excel, export_sql, export_zip
from .extractor import extract_workbook
from .mapper import build_normalized_tables, derive_site_ref_key

logger = logging.getLogger(__name__)


def process_onboarding_file(input_path, party_id="SEKURA", site_ref_key=None):
    workbook = extract_workbook(input_path)
    site_ref_key = site_ref_key or derive_site_ref_key(workbook)
    tables = build_normalized_tables(workbook, party_id=party_id, site_ref_key=site_ref_key)

    run_id = uuid4().hex[:10]
    output_dir = Path(settings.MEDIA_ROOT) / "onboarding" / "outputs" / run_id
    excel_path = output_dir / f"Solardb_{site_ref_key}.xlsx"
    sql_path = output_dir / f"onboarding_{site_ref_key}.sql"
    zip_path = output_dir / f"onboarding_{site_ref_key}.zip"

    export_excel(tables, excel_path)
    export_sql(tables, sql_path)
    export_zip([excel_path, sql_path], zip_path)

    summary = {
        "party_id": party_id,
        "site_ref_key": site_ref_key,
        "sheets": {name: int(len(df)) for name, df in tables.items()},
        "warnings": workbook.warnings,
    }
    logger.info("Onboarding export generated for %s: %s", site_ref_key, summary)
    return {
        "workbook": workbook,
        "tables": tables,
        "excel_path": excel_path,
        "sql_path": sql_path,
        "zip_path": zip_path,
        "summary": summary,
    }


def validate_only(input_path):
    try:
        workbook = extract_workbook(input_path)
    except ValidationError:
        raise
    return {
        "site_details": workbook.site_details,
        "sheets": {name: int(len(df)) for name, df in workbook.sheets.items()},
        "warnings": workbook.warnings,
    }
