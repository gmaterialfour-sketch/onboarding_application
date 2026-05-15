from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
from django.test import SimpleTestCase, override_settings

from .services.hierarchy import generate_assets
from .services.pipeline import process_onboarding_file


class OnboardingPipelineTests(SimpleTestCase):
    def _workbook(self, path):
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            pd.DataFrame(
                [
                    ["Solar Site Details", None, None],
                    ["Site Name", "Demo Solar Plant", None],
                    ["Capacity", 10, "MW"],
                ]
            ).to_excel(writer, sheet_name="Solar Site Details", header=False, index=False)
            pd.DataFrame(
                [
                    {
                        "PV Module Name": "Module A",
                        "No. of Panels": 20,
                        "Rating": 540,
                        "Pv panel make": "Longi",
                        "Panel Type": "Bifacial",
                        "PV Panel efficiency": 0.21,
                        "Panel Size(Sq. meter)": 2.5,
                        "Total Panel Area": 50,
                    }
                ]
            ).to_excel(writer, sheet_name="PVModules", index=False)
            pd.DataFrame(
                [
                    {
                        "ITS--INV-M": "ITS-1-INV-1-M1",
                        "Inverter Name": "Inverter -1",
                        "Make": "Sungrow",
                        "Model": "SG4400UD",
                        "Controller Ids": "172.16.1.8",
                        "Block wise name": "B-1",
                        "SCB name": "ITS-1-INV-1-M1-1",
                        "String/scb": 2,
                    }
                ]
            ).to_excel(writer, sheet_name="Inverter", index=False)
            pd.DataFrame(
                [
                    {
                        "ITS-INV-M": "ITS-1-INV-1-M1",
                        "SCB No.": 1,
                        "Total No.of String Connected": 2,
                        "DC Loading (kW)": 223.3,
                        "Block wise name": "B-1",
                    }
                ]
            ).to_excel(writer, sheet_name="Inverter wise String Connected", index=False)
            pd.DataFrame([{"S.N": 1, "Meter Type": "ABT Meter", "Controller ID": "10.0.0.1"}]).to_excel(
                writer, sheet_name="Meter", index=False
            )
            pd.DataFrame([{"S.N": 1, "Device Name": "Data logger", "Controller ID": "10.0.0.2"}]).to_excel(
                writer, sheet_name="Weather", index=False
            )
            pd.DataFrame([["DGR Report", "Mandatory", "Available"]]).to_excel(
                writer, sheet_name="Documents", header=False, index=False
            )

    def test_pipeline_generates_excel_sql_and_zip(self):
        with TemporaryDirectory() as temp_dir:
            media_root = Path(temp_dir) / "media"
            input_path = Path(temp_dir) / "input.xlsx"
            self._workbook(input_path)
            with override_settings(MEDIA_ROOT=media_root):
                result = process_onboarding_file(input_path, party_id="TEST")

            self.assertTrue(result["excel_path"].exists())
            self.assertTrue(result["sql_path"].exists())
            self.assertTrue(result["zip_path"].exists())
            self.assertGreater(result["summary"]["sheets"]["asset_master"], 5)
            self.assertIn("mqtt_mapping", result["tables"])
            self.assertIn("INSERT INTO ods.asset_master", result["sql_path"].read_text(encoding="utf-8"))

    def test_mod_numbering_resets_for_each_inverter(self):
        workbook = type(
            "Workbook",
            (),
            {
                "site_details": {"SITE_NAME": "Demo Solar Plant"},
                "sheets": {
                    "Inverter": pd.DataFrame(
                        [
                            {"ITS--INV-M": "ITS-1-INV-85-M1", "Inverter Name": "Inverter 85", "Block wise name": "B-43"},
                            {"ITS--INV-M": "ITS-1-INV-85-M2", "Inverter Name": "Inverter 85", "Block wise name": "B-43"},
                            {"ITS--INV-M": "ITS-1-INV-86-M1", "Inverter Name": "Inverter 86", "Block wise name": "B-43"},
                            {"ITS--INV-M": "ITS-1-INV-86-M2", "Inverter Name": "Inverter 86", "Block wise name": "B-43"},
                        ]
                    )
                },
            },
        )()

        result = generate_assets(workbook, "TEST", "BEPL_SITE1")
        mod_keys = [asset["asset_ref_key"] for asset in result["assets"] if asset["asset_class_key"] == "MOD"]

        self.assertEqual(
            mod_keys,
            [
                "BEPL_SITE1_BLK43_INV1_MOD1",
                "BEPL_SITE1_BLK43_INV1_MOD2",
                "BEPL_SITE1_BLK43_INV2_MOD1",
                "BEPL_SITE1_BLK43_INV2_MOD2",
            ],
        )

# Create your tests here.
