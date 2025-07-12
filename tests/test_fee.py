import unittest
from datetime import datetime
import os
from ps_camp.repos.post_sql_repo import calculate_post_fee


class TestPostFeeCalculation(unittest.TestCase):
    def setUp(self):
        os.environ["CAMP_START_DATE"] = "2025-07-01"

    def test_day1_non_golden(self):
        dt = datetime(2025, 7, 1, 10, 0).astimezone()
        self.assertEqual(calculate_post_fee(dt), 300000)

    def test_day1_golden(self):
        dt = datetime(2025, 7, 1, 18, 30).astimezone()
        self.assertEqual(calculate_post_fee(dt), 350000)

    def test_day3_golden(self):
        dt = datetime(2025, 7, 3, 19, 0).astimezone()
        self.assertEqual(calculate_post_fee(dt), 1200000)

    def test_day4_non_golden(self):
        dt = datetime(2025, 7, 4, 10, 0).astimezone()
        self.assertEqual(calculate_post_fee(dt), 1200000)

    def test_day5_anytime(self):
        dt = datetime(2025, 7, 5, 14, 0).astimezone()
        self.assertEqual(calculate_post_fee(dt), 300000)


if __name__ == "__main__":
    unittest.main()
