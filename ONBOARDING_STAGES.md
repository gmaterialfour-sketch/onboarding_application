# Solar Onboarding Engine Stages

## Big Idea

```text
Client Excel
      |
      v
Python Logic
      |
      v
Standardized Data
      |
      v
Hierarchy
      |
      v
SQL
      |
      v
Database
```

This backend is an Excel-to-database onboarding engine for solar SCADA assets.

In simple words:

```text
Cleaning data
-> organizing data
-> naming data properly
-> connecting assets
-> converting to DB format
-> uploading to system
```

## Stage 1: Read Client Excel

The client gives an onboarding Excel file.

Common input sheets:

```text
Solar Site Details
PVModules
Inverter
Meter
Weather
Inverter wise String Connected
Documents
```

The system reads the workbook using Pandas.

Example:

```python
import pandas as pd

inv_df = pd.read_excel(file, sheet_name="Inverter")
```

After this step, Excel becomes table-like data called a DataFrame.

Project files:

- `onboarding/views.py`
- `onboarding/serializers.py`
- `onboarding/services/extractor.py`

## Stage 2: Validate and Clean Data

Client files are not always perfect.

Problems can include:

- Missing sheets
- Missing columns
- Empty rows
- Duplicate rows
- Merged or shifted headers
- Extra spaces
- `NaN` values

The extractor validates required sheets and columns before processing.

Example logic:

```python
REQUIRED_SHEETS = {
    "PVModules": ["pvmodules", "pv module"],
    "Inverter": ["inverter", "inverters"],
}
```

Project files:

- `onboarding/services/extractor.py`
- `onboarding/services/exceptions.py`
- `onboarding/services/utils.py`

## Stage 3: Standardize Data

Every client may use different names.

Example:

| Client A | Client B   | Company Format |
| -------- | ---------- | -------------- |
| INV-1    | Inverter_1 | INV1           |
| SG1      | Sungrow1   | SG1            |

So the system creates rules to normalize names.

Example:

```python
def standardize_inverter_name(name):
    return name.upper().replace("-", "").replace("_", "")
```

Input:

```text
INV-1
```

Output:

```text
INV1
```

Now all client formats become one standard format.

Project files:

- `onboarding/services/utils.py`
- `onboarding/services/mapper.py`

## Stage 4: Create `asset_ref_key`

The `asset_ref_key` is the unique ID of every asset.

It works like:

- Aadhaar number
- Employee ID
- Roll number
- Serial number

Example structure:

```text
SITE_BLOCK_ASSET
```

Example:

```text
BEPL_BLK1_INV1
```

Python logic:

```python
site = "BEPL"
block = "BLK1"
inv = "INV1"

asset_ref_key = f"{site}_{block}_{inv}"
```

Result:

```text
BEPL_BLK1_INV1
```

In the project, keys are generated automatically for:

- SITE
- BLOCK
- INVERTER
- MOD
- SCB
- STRING
- PV_MODULE
- METER
- WEATHER

Project files:

- `onboarding/services/hierarchy.py`
- `onboarding/services/utils.py`

## Stage 5: Build Hierarchy

The system must know who belongs to whom.

Example:

```text
SCB1 belongs to INV1
INV1 belongs to BLK1
BLK1 belongs to SITE
```

Tree structure:

```text
SITE
 ├── BLOCK
 │    ├── INVERTER
 │    │    ├── MOD
 │    │    │    ├── SCB
 │    │    │    │    ├── STRING
```

This becomes parent-child mapping.

Example:

| asset_ref_key       | container_ref_key |
| ------------------- | ----------------- |
| BEPL_BLK1_INV1      | BEPL_BLK1         |
| BEPL_BLK1_INV1_SCB1 | BEPL_BLK1_INV1    |

Python logic:

```python
hierarchy = []

hierarchy.append({
    "asset_ref_key": "BEPL_BLK1_INV1",
    "container_ref_key": "BEPL_BLK1",
})
```

Project file:

- `onboarding/services/hierarchy.py`

## Stage 6: Create `asset_attr_master`

Every asset needs properties.

Example inverter properties:

- MAKE
- MODEL
- CAPACITY
- CONTROLLER_ID

Python logic:

```python
rows = []

rows.append({
    "asset_ref_key": "BEPL_BLK1_INV1",
    "attr_key": "MAKE",
    "attr_value": "Sungrow",
})
```

Result:

| asset_ref_key  | attr_key | attr_value |
| -------------- | -------- | ---------- |
| BEPL_BLK1_INV1 | MAKE     | Sungrow    |

Project file:

- `onboarding/services/hierarchy.py`

## Stage 7: Create `asset_master`

`asset_master` defines what type of asset each key represents.

Example:

| asset_ref_key  | asset_class_key |
| -------------- | --------------- |
| BEPL_BLK1_INV1 | INVERTER        |
| BEPL_BLK1_SCB1 | SCB             |

Python logic:

```python
asset = {
    "asset_ref_key": "BEPL_BLK1_INV1",
    "asset_class_key": "INVERTER",
}
```

Project files:

- `onboarding/services/hierarchy.py`
- `onboarding/services/mapper.py`

## Stage 8: Create Telemetry and MQTT Mapping

The system also creates measurement rules.

Example inverter telemetry:

- AC_POWER
- AC_CURRENT
- AC_VOLTAGE
- DC_POWER
- STATUS

Example MQTT topic:

```text
bepl_site001/inverter/bepl_site001_blk001_inv001/ac_power
```

Project files:

- `onboarding/services/telemetry.py`
- `onboarding/services/mqtt.py`

## Stage 9: Generate SQL

Now the normalized rows are converted into SQL insert statements.

Input table row:

| asset_ref_key | attr_key | attr_value |
| ------------- | -------- | ---------- |
| INV1          | MAKE     | Sungrow    |

Generated SQL:

```sql
INSERT INTO asset_attr_master
(asset_ref_key, attr_key, attr_value)
VALUES
('INV1', 'MAKE', 'Sungrow');
```

Python SQL generator idea:

```python
query = f"""
INSERT INTO asset_attr_master
(asset_ref_key, attr_key, attr_value)
VALUES
('{ref}', '{attr}', '{value}');
"""
```

In the project, SQL generation is safer and reusable. It loops over normalized DataFrames and creates PostgreSQL-compatible insert scripts.

Project file:

- `onboarding/services/sql_generator.py`

## Stage 10: Write Output Excel

The system writes standardized output sheets into a new Excel file.

Using:

- Pandas `ExcelWriter`
- Openpyxl formatting

Generated sheets include:

- party
- asset_class
- asset_master
- asset_hierarchy
- asset_class_attr_meas
- asset_attr_master
- mqtt_mapping
- equipment
- telemetry_mapping

Output file example:

```text
Solardb_BEPL_SITE001.xlsx
```

Project file:

- `onboarding/services/exporter.py`

## Stage 11: Create Download Package

Final generated files:

- `Solardb_<SITE>.xlsx`
- `onboarding_<SITE>.sql`
- `onboarding_<SITE>.zip`

Project file:

- `onboarding/services/pipeline.py`

## Final Flow

```text
INPUT
Client Excel

|
v

PROCESSING
Python reads data

|
v

STANDARDIZATION
Names normalized

|
v

KEY GENERATION
Create asset_ref_key

|
v

HIERARCHY
Create parent-child relationships

|
v

MAPPING
Create asset_master
Create asset_attr_master
Create asset_hierarchy
Create telemetry_mapping
Create mqtt_mapping

|
v

SQL GENERATION
Create INSERT queries

|
v

OUTPUT
Excel mapping file
SQL files
ZIP package

|
v

DATABASE
Upload into PostgreSQL
```

## Industry Names

| Concept            | Industry Name        |
| ------------------ | -------------------- |
| Excel to DB system | ETL pipeline         |
| Asset hierarchy    | Domain modeling      |
| Key generation     | Identity mapping     |
| Parent-child links | Relational hierarchy |
| SQL generation     | Data onboarding      |
| Standardization    | Data normalization   |

## Simplest Understanding

This system takes messy engineering Excel data and turns it into database-ready onboarding data.

The whole logic is:

```text
Read Excel
-> clean it
-> standardize names
-> generate unique asset IDs
-> build hierarchy
-> create normalized tables
-> generate SQL
-> load into PostgreSQL
```
