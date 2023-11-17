import unittest

from scripts.update_capacity_configuration import (
    update_capacity_config,
    update_capacity_list,
)


class updateCapacityConfigurationTestCase(unittest.TestCase):
    def test_capacity_config(self):
        capacity_config = {
            "wind": 1,
            "solar": {"datetime": "2022-01-01", "value": 2, "source": "abc"},
            "biomass": [
                {"datetime": "2022-01-01", "value": 3, "source": "abc"},
                {"datetime": "2023-01-01", "value": 4, "source": "abc"},
            ],
            "unknown": [
                {"datetime": "2022-01-01", "value": 3, "source": "abc"},
                {"datetime": "2022-10-01", "value": 4, "source": "abc"},
            ],
        }
        data = {
            "wind": {"datetime": "2023-01-01", "value": 3, "source": "abc"},
            "solar": {"datetime": "2023-01-01", "value": 4, "source": "abc"},
            "biomass": {"datetime": "2023-01-01", "value": 5, "source": "abc"},
            "hydro": {"datetime": "2023-01-01", "value": 6, "source": "abc"},
            "unknown": {"datetime": "2023-01-01", "value": 5, "source": "abc"},
        }

        expected = {
            "wind": {"datetime": "2023-01-01", "value": 3, "source": "abc"},
            "solar": [
                {"datetime": "2022-01-01", "value": 2, "source": "abc"},
                {"datetime": "2023-01-01", "value": 4, "source": "abc"},
            ],
            "biomass": [
                {"datetime": "2022-01-01", "value": 3, "source": "abc"},
                {"datetime": "2023-01-01", "value": 5, "source": "abc"},
            ],
            "hydro": {"datetime": "2023-01-01", "value": 6, "source": "abc"},
            "unknown": [
                {"datetime": "2022-01-01", "value": 3, "source": "abc"},
                {"datetime": "2022-10-01", "value": 4, "source": "abc"},
                {"datetime": "2023-01-01", "value": 5, "source": "abc"},
            ],
        }

        self.assertEqual(update_capacity_config(capacity_config, data), expected)

    def test_update_capacity_list(self):
        capacity_config = {
            "biomass": [
                {"datetime": "2022-01-01", "value": 3, "source": "abc"},
                {"datetime": "2023-01-01", "value": 4, "source": "abc"},
            ],
            "unknown": [
                {"datetime": "2022-01-01", "value": 3, "source": "abc"},
                {"datetime": "2022-10-01", "value": 4, "source": "abc"},
            ],
        }

        data = {
            "biomass": {"datetime": "2023-01-01", "value": 5, "source": "abc"},
            "unknown": {"datetime": "2023-01-01", "value": 5, "source": "abc"},
        }

        expected = {
            "biomass": [
                {"datetime": "2022-01-01", "value": 3, "source": "abc"},
                {"datetime": "2023-01-01", "value": 5, "source": "abc"},
            ],
            "unknown": [
                {"datetime": "2022-01-01", "value": 3, "source": "abc"},
                {"datetime": "2022-10-01", "value": 4, "source": "abc"},
                {"datetime": "2023-01-01", "value": 5, "source": "abc"},
            ],
        }

        self.assertEqual(
            update_capacity_list("unknown", capacity_config, data), expected["unknown"]
        )
        self.assertEqual(
            update_capacity_list("biomass", capacity_config, data), expected["biomass"]
        )
