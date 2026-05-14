import logging
from dataclasses import dataclass, field

import pandas as pd

from .exceptions import ValidationError
from .utils import clean_dataframe, clean_text

logger = logging.getLogger(__name__)


REQUIRED_SHEETS = {
    "Solar Site Details": ["solar site details", "site details"],
    "PVModules": ["pvmodules", "pv module", "pv_modules"],
    "Inverter": ["inverter", "inverters"],
    "Inverter wise String Connected": ["inverter wise string connected", "string connected"],
    "Meter": ["meter", "meters"],
    "Weather": ["weather", "wms"],
    "Documents": ["documents", "document"],
}

REQUIRED_COLUMNS = {
    "PVModules": ["PV Module Name", "No. of Panels", "Rating"],
    "Inverter": ["Inverter Name", "Make", "Model", "Block wise name"],
    "Inverter wise String Connected": ["ITS-INV-M", "SCB No.", "Total No.of String Connected", "Block wise name"],
    "Meter": ["Meter Type"],
    "Weather": ["Device Name", "Controller ID"],
}


@dataclass
class WorkbookData:
    path: str
    sheets: dict = field(default_factory=dict)
    site_details: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)


def _norm(value):
    return clean_text(value).lower().replace("_", "").replace("-", "").replace(" ", "")


def find_sheet(sheet_names, canonical):
    candidates = REQUIRED_SHEETS[canonical]
    normalized = {_norm(name): name for name in sheet_names}
    for candidate in candidates:
        if _norm(candidate) in normalized:
            return normalized[_norm(candidate)]
    for name in sheet_names:
        if any(_norm(candidate) in _norm(name) for candidate in candidates):
            return name
    return None


def _detect_header_row(path, sheet_name, expected_columns=None, max_rows=12):
    raw = pd.read_excel(path, sheet_name=sheet_name, header=None, nrows=max_rows)
    expected = {_norm(col) for col in expected_columns or []}
    best_row = 0
    best_score = -1
    for idx, row in raw.iterrows():
        values = {_norm(v) for v in row.tolist() if clean_text(v)}
        score = len(values & expected) if expected else len(values)
        if score > best_score:
            best_score = score
            best_row = idx
    return best_row


def _read_table(path, sheet_name, expected_columns=None):
    header_row = _detect_header_row(path, sheet_name, expected_columns)
    df = pd.read_excel(path, sheet_name=sheet_name, header=header_row)
    return clean_dataframe(df)


def _extract_site_details(path, sheet_name):
    raw = pd.read_excel(path, sheet_name=sheet_name, header=None)
    details = {}
    for _, row in raw.iterrows():
        values = [clean_text(v) for v in row.tolist()]
        for idx, value in enumerate(values):
            if not value:
                continue
            key = value.upper().replace(" ", "_")
            if key in {"CUSTOMER", "SITE_NAME", "SITE_ADDRESS", "CAPACITY", "EMAIL_ID", "CONTACT_NUMBER", "END_CUSTOMER"}:
                next_value = ""
                for candidate in values[idx + 1 :]:
                    if candidate:
                        next_value = candidate
                        break
                if next_value:
                    details[key] = next_value
    return details


def validate_workbook(workbook):
    errors = []
    for sheet_name, aliases in REQUIRED_SHEETS.items():
        if sheet_name not in workbook.sheets and sheet_name != "Solar Site Details":
            errors.append(f"Missing required sheet: {sheet_name} ({', '.join(aliases)})")
    for sheet_name, columns in REQUIRED_COLUMNS.items():
        df = workbook.sheets.get(sheet_name)
        if df is None:
            continue
        available = {_norm(col) for col in df.columns}
        for col in columns:
            if _norm(col) not in available:
                errors.append(f"Missing column in {sheet_name}: {col}")
    if errors:
        raise ValidationError("Workbook validation failed", errors)


def extract_workbook(path):
    logger.info("Extracting workbook %s", path)
    workbook = WorkbookData(path=str(path))
    with pd.ExcelFile(path) as xl:
        sheet_names = xl.sheet_names

    site_sheet = find_sheet(sheet_names, "Solar Site Details")
    if site_sheet:
        workbook.site_details = _extract_site_details(path, site_sheet)
    else:
        workbook.warnings.append("Solar Site Details sheet not found")

    for canonical in REQUIRED_SHEETS:
        if canonical == "Solar Site Details":
            continue
        actual = find_sheet(sheet_names, canonical)
        if not actual:
            continue
        workbook.sheets[canonical] = _read_table(path, actual, REQUIRED_COLUMNS.get(canonical))

    validate_workbook(workbook)
    return workbook
