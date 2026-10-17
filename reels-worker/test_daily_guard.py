import importlib.util
import json
import pathlib
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('guard', pathlib.Path(__file__).with_name('daily_guard.py'))
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
PRICE = 'standard rates are $0.084 per second for 1 second clips and $0.126 per second for 3 or 15 second clips'

class BudgetTests(unittest.TestCase):
    def setup_root(self, directory):
        root = pathlib.Path(directory)
        (root/'automation.json').write_text(json.dumps({'enabled': True, 'daily_budget_usd': '0.65', 'model': guard.MODEL, 'duration_seconds': 5}))
        return root

    def test_reservation_blocks_second_attempt_after_failure(self):
        with tempfile.TemporaryDirectory(dir=pathlib.Path(__file__).parent) as directory:
            root = self.setup_root(directory)
            guard.reserve(root, '2026-10-18', PRICE, commit=False)
            with self.assertRaisesRegex(RuntimeError, 'already reserved'):
                guard.reserve(root, '2026-10-18', PRICE, commit=False)
            guard.reserve(root, '2026-10-19', PRICE, commit=False)

    def test_price_increase_and_unknown_price_stop_before_reserving(self):
        for page in [PRICE.replace('0.126', '0.150'), 'unavailable']:
            with tempfile.TemporaryDirectory(dir=pathlib.Path(__file__).parent) as directory:
                root = self.setup_root(directory)
                with self.assertRaises(RuntimeError):
                    guard.reserve(root, '2026-10-18', page, commit=False)
                self.assertFalse((root/'ai-daily-ledger.json').exists())

    def test_raised_budget_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=pathlib.Path(__file__).parent) as directory:
            root = self.setup_root(directory)
            config = json.loads((root/'automation.json').read_text())
            config['daily_budget_usd'] = '1'
            (root/'automation.json').write_text(json.dumps(config))
            with self.assertRaisesRegex(RuntimeError, 'authorized'):
                guard.reserve(root, '2026-10-18', PRICE, commit=False)

if __name__ == '__main__':
    unittest.main()

