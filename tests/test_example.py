import unittest
from pathlib import Path

from prefect import flow, task

from astropy.coordinates import EarthLocation

from check.example import (
    location_from_astropy,
    observatory_file,
    location_from_fits,
    tune_location,
    geodetic_info,
    example,
)


class TestExampleTasks(unittest.TestCase):
    srt_fits = Path(__file__).parent / "data" / "xyz.fits"

    def test_location_from_astropy_description(self):
        self.assertIn("from Astropy", location_from_astropy.description)

    def test_location_from_astropy(self):
        loc = location_from_astropy.fn("Medicina")
        self.assertEqual(loc.info.name, "Medicina Radio Telescope")

    def test_observatory_file_description(self):
        self.assertIn("FITS file produced", observatory_file.description)

    def test_observatory_file_found(self):
        file_path = observatory_file.fn("SRT")  # Absolute file name
        self.assertEqual(file_path.name, "xyz.fits")

    def test_observatory_file_not_found_error(self):
        with self.assertRaises(FileNotFoundError):
            observatory_file.fn("SRT", "/file/does/not/exist")

    def test_observatory_file_location_not_found(self):
        with self.assertRaisesRegex(ValueError, "No FITS file"):
            observatory_file.fn("Medicina")

    def test_location_from_fits_description(self):
        self.assertIn("Location from FITS", location_from_fits.description)

    def test_location_from_fits(self):
        loc = location_from_fits.fn(self.srt_fits)
        self.assertAlmostEqual(loc.height.value, 650)
        self.assertEqual(loc.info.name, "SRT")

    def test_tune_location_description(self):
        self.assertIn("Tune observatory location", tune_location.description)

    def test_tune_location(self):
        loc_a = EarthLocation.of_site("SRT")
        loc_b = location_from_fits.fn(self.srt_fits)
        loc = tune_location.fn(loc_a, loc_b)
        average_height = (loc_a.height.value + loc_b.height.value) / 2
        self.assertAlmostEqual(loc.height.value, average_height)

    def test_tune_location_different_sites(self):
        loc_a = EarthLocation.of_site("Medicina")
        loc_b = location_from_fits.fn(self.srt_fits)
        with self.assertRaisesRegex(ValueError, "Locations do not refer"):
            tune_location.fn(loc_a, loc_b)

    def test_geodetic_info_description(self):
        self.assertIn("Geodetic information of", geodetic_info.description)

    def test_geodetic_info(self):
        loc = EarthLocation.of_site("Medicina")
        info = geodetic_info.fn(loc)
        self.assertEqual(info["observatory"], "Medicina Radio Telescope")
        self.assertAlmostEqual(info["latitude"], 44.5205)
        self.assertAlmostEqual(info["longitude"], 11.6469)
        self.assertAlmostEqual(info["height"], 25)


class TestExampleFlow(unittest.TestCase):
    def test_example(self):
        info = example("SRT")
        self.assertEqual(info["observatory"], "Sardinia Radio Telescope")
        self.assertAlmostEqual(info["latitude"], 39.5, 1)
        self.assertAlmostEqual(info["longitude"], 9.2, 1)
        self.assertAlmostEqual(info["height"], 660.8, 1)
