import zipfile
from pathlib import Path

from openpyxl.styles import Font, PatternFill

from .sql_generator import generate_sql


EXPORT_SHEETS = [
    "party",
    "asset_class",
    "asset_master",
    "asset_hierarchy",
    "asset_class_attr_meas",
    "asset_attr_master",
    "mqtt_mapping",
    "equipment",
    "telemetry_mapping",
]


def export_excel(tables, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with __import__("pandas").ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name in EXPORT_SHEETS:
            df = tables.get(sheet_name)
            if df is None:
                continue
            df.to_excel(writer, sheet_name=sheet_name[:31], index=False)

        workbook = writer.book
        for worksheet in workbook.worksheets:
            for cell in worksheet[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="1F4E78")
            worksheet.freeze_panes = "A2"
            for column_cells in worksheet.columns:
                max_length = max(len(str(cell.value or "")) for cell in column_cells)
                worksheet.column_dimensions[column_cells[0].column_letter].width = min(max(max_length + 2, 12), 50)
    return output_path


def export_sql(tables, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(generate_sql(tables), encoding="utf-8")
    return output_path


def export_zip(files, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in files:
            file_path = Path(file_path)
            archive.write(file_path, arcname=file_path.name)
    return output_path
