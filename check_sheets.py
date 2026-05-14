import pandas as pd

path = r"C:\Users\NT105082\Downloads\Onboarding Details_350Mw BEPL Site (1).xlsx"
xl = pd.ExcelFile(path)
print(f"DEBUG_SHEETS: {xl.sheet_names}")
