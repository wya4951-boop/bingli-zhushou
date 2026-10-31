"""Synthetic calendar cases; no clinical records or external dependencies."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'transplant_day.py'
spec = importlib.util.spec_from_file_location('transplant_day', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CalendarTests(unittest.TestCase):
    def test_single_calendar_boundaries(self):
        for event, transplant, expected in [
            ('2032-02-28', '2032-02-28', '0d'),
            ('2032-02-29', '2032-02-28', '+1d'),
            ('2032-03-01', '2032-02-28', '+2d'),
            ('2033-01-01', '2032-12-31', '+1d')]:
            with self.subTest(event=event):
                self.assertEqual(module.transplant_day(event, [transplant])['label'], expected)

    def test_two_infusions_and_gap(self):
        dates = ['2032-02-28', '2032-03-01']
        for event, label, status in [
            ('2032-02-27', None, 'before_transplant'),
            ('2032-02-28', '01d', 'resolved'),
            ('2032-02-29', None, 'between_infusions_confirm_convention'),
            ('2032-03-01', '02d', 'resolved'),
            ('2032-03-02', '+1d', 'resolved')]:
            with self.subTest(event=event):
                result = module.transplant_day(event, dates)
                self.assertEqual((result['label'], result['status']), (label, status))

    def test_invalid_dates(self):
        for bad in ['20320228', '2032-W09-1', '2032-2-28', '2031-02-29',
                    '2032-04-31', '0000-01-01', '2032-02-28T00:00:00', '', None, 20320228]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                module.transplant_day(bad, ['2032-02-28'])
            with self.subTest(transplant=bad), self.assertRaises(ValueError):
                module.transplant_day('2032-03-02', [bad])

    def test_invalid_infusion_sets(self):
        for bad in [None, '2032-02-28', [], ['2032-02-28'] * 3,
                    ['2032-02-28'] * 2, ['2032-03-01', '2032-02-28']]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                module.transplant_day('2032-03-02', bad)

    def test_cli_success_and_failure(self):
        good = subprocess.run([sys.executable, str(SCRIPT), '--date', '2032-03-02',
                               '--transplant', '2032-02-28', '2032-03-01'], capture_output=True, text=True)
        self.assertEqual(good.returncode, 0)
        self.assertEqual(json.loads(good.stdout)['label'], '+1d')
        bad = subprocess.run([sys.executable, str(SCRIPT), '--date', '20320228',
                              '--transplant', '2032-02-28'], capture_output=True, text=True)
        self.assertNotEqual(bad.returncode, 0)
        self.assertEqual(bad.stdout, '')


if __name__ == '__main__':
    unittest.main()
