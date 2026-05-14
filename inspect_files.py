import pandas as pd

def inspect_excel(path):
    print(f"\n--- Inspecting: {path} ---")
    try:
        xl = pd.ExcelFile(path)
        print(f"Sheets: {xl.sheet_names}")
        for sheet in xl.sheet_names[:5]: # Inspect first 5 sheets
            df = pd.read_excel(path, sheet_name=sheet).head(3)
            print(f"\nSheet: {sheet}")
            print(df.columns.tolist())
            print(df.values.tolist())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_excel(r"C:\Users\NT105082\Downloads\Onboarding Details_350Mw BEPL Site (1).xlsx")
    inspect_excel(r"C:\Users\NT105082\Downloads\Solardb_BEPL.xlsx")
