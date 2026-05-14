import re
from collections import defaultdict
from decimal import Decimal, InvalidOperation

import pandas as pd


def clean_text(value):
    if pd.isna(value):
        return ""
    text = str(value).replace("\xa0", " ").strip()
    return re.sub(r"\s+", " ", text)


def slug_key(value, fallback="ITEM"):
    text = clean_text(value).upper()
    text = re.sub(r"[^A-Z0-9]+", "_", text).strip("_")
    return text or fallback


def normalize_columns(columns):
    seen = defaultdict(int)
    normalized = []
    for col in columns:
        name = clean_text(col)
        name = name if name and not name.lower().startswith("unnamed") else "column"
        seen[name] += 1
        if seen[name] > 1:
            name = f"{name}_{seen[name]}"
        normalized.append(name)
    return normalized


def clean_dataframe(df):
    df = df.dropna(how="all").copy()
    df.columns = normalize_columns(df.columns)
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].map(clean_text)
    return df.drop_duplicates().reset_index(drop=True)


def sql_literal(value):
    if value is None or (isinstance(value, float) and pd.isna(value)) or value == "":
        return "''"
    if isinstance(value, str) and value.lower() == "now()":
        return "now()"
    if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        return str(value)
    text = clean_text(value).replace("'", "''")
    return f"'{text}'"


def first_present(row, names, default=""):
    for name in names:
        if name in row and clean_text(row.get(name)):
            return row.get(name)
    return default


def parse_int(value, default=0):
    try:
        if pd.isna(value) or value == "":
            return default
        return int(float(value))
    except (ValueError, TypeError):
        return default


def parse_decimal(value, default=""):
    try:
        if pd.isna(value) or value == "":
            return default
        return str(Decimal(str(value)).normalize())
    except (InvalidOperation, ValueError, TypeError):
        return default


class KeyGenerator:
    def __init__(self):
        self._counters = defaultdict(int)

    def next(self, prefix):
        self._counters[prefix] += 1
        return f"{prefix}{self._counters[prefix]}"
