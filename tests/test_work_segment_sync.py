"""Wails の勤務区分キーと Python の定義がずれないことを確認する。"""

import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from work_segment import HrmosWorkSegment  # noqa: E402


class WorkSegmentSyncTest(unittest.TestCase):
    def test_wails_segment_keys_match_python_enum(self):
        source = (ROOT / "desktop/frontend/src/App.tsx").read_text(encoding="utf-8")
        block = re.search(r"const segments = \[(.*?)\n\];", source, re.DOTALL)
        self.assertIsNotNone(block, "Wails の勤務区分一覧が見つかりません")
        keys = re.findall(r"\['([A-Z_]+)',\s*'[^']*'\]", block.group(1))
        self.assertTrue(keys, "Wails の勤務区分キーを読み取れません")
        self.assertEqual(len(keys), len(set(keys)), "Wails に勤務区分キーの重複があります")
        self.assertEqual(set(keys), set(HrmosWorkSegment.__members__))


if __name__ == "__main__":
    unittest.main()
