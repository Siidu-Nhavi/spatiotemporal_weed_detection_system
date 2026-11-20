import io
import sys
import unittest
from pathlib import Path

import numpy as np
import rasterio
from fastapi.testclient import TestClient
from rasterio.transform import from_origin

sys.path.insert(0, str(Path(__file__).parents[1]))

from app.main import app


PROJECT_ROOT = Path(__file__).parents[2]


class AnalysisWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.cwfid_image = (
            PROJECT_ROOT / "datasets" / "raw" / "CWFID" / "images" / "001_image.png"
        )

    def test_real_cwfid_image_analysis_contract(self):
        response = self.client.post(
            "/api/analyze",
            files={
                "image": (
                    self.cwfid_image.name,
                    self.cwfid_image.read_bytes(),
                    "image/png",
                )
            },
            data={"rows": "4", "columns": "4"},
        )

        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(result["image"]["width"], 1296)
        self.assertEqual(result["image"]["height"], 966)
        self.assertEqual(result["coordinate_system"], "image_pixels")
        self.assertEqual(len(result["grid"]["cells"]), 16)
        self.assertIn(result["detection"]["mode"], {"custom_model", "demo"})
        self.assertGreaterEqual(result["detection"]["weed_coverage_percent"], 0)
        self.assertLessEqual(result["detection"]["weed_coverage_percent"], 100)

    def test_geotiff_analysis_and_exports_preserve_crs(self):
        source = io.BytesIO()
        with rasterio.open(
            source,
            "w",
            driver="GTiff",
            width=16,
            height=12,
            count=3,
            dtype="uint8",
            crs="EPSG:32633",
            transform=from_origin(500000, 4600000, 10, 10),
        ) as dataset:
            for band in range(1, 4):
                dataset.write(np.full((12, 16), band * 20, dtype=np.uint8), band)

        source_bytes = source.getvalue()
        response = self.client.post(
            "/api/analyze",
            files={"image": ("fixture.tif", source_bytes, "image/tiff")},
            data={"rows": "2", "columns": "2"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(result["coordinate_system"], "geographic")
        self.assertEqual(result["geospatial"]["crs"], "EPSG:32633")
        self.assertIn("spatial_coordinates", result["grid"]["cells"][0])

        geojson = self.client.post(
            "/api/export",
            files={"image": ("fixture.tif", source_bytes, "image/tiff")},
            data={"export_format": "geojson", "rows": "2", "columns": "2"},
        )
        self.assertEqual(geojson.status_code, 200, geojson.text)
        self.assertEqual(geojson.json()["type"], "FeatureCollection")
        self.assertEqual(len(geojson.json()["features"]), 4)

        exported = self.client.post(
            "/api/export",
            files={"image": ("fixture.tif", source_bytes, "image/tiff")},
            data={"export_format": "geotiff"},
        )
        self.assertEqual(exported.status_code, 200, exported.text)
        with rasterio.open(io.BytesIO(exported.content)) as dataset:
            self.assertEqual(dataset.crs.to_string(), "EPSG:32633")
            self.assertEqual((dataset.width, dataset.height), (16, 12))
            self.assertEqual(dataset.count, 1)


if __name__ == "__main__":
    unittest.main()
