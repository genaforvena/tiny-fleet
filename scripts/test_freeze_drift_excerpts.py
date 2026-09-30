#!/usr/bin/env python3
import unittest

from freeze_drift_excerpts import select_common_source_path


class HeldoutExcerptSelectionTests(unittest.TestCase):
    def test_selection_is_stable_and_uses_common_native_modules(self):
        old = ["src/flask/a.py", "src/flask/b.py", "src/flask/tests/test_api.py"]
        new = ["src/flask/b.py", "src/flask/a.py", "src/flask/tests/test_api.py"]
        selected = select_common_source_path("flask", old, new, "src/flask", "src/flask")
        reversed_selection = select_common_source_path("flask", list(reversed(old)), list(reversed(new)), "src/flask", "src/flask")
        self.assertEqual(selected, reversed_selection)
        self.assertIn(selected[0], {"a.py", "b.py"})
        self.assertEqual(selected[1], "src/flask/" + selected[0])
        self.assertEqual(selected[2], "src/flask/" + selected[0])

    def test_no_common_native_module_is_a_typed_failure(self):
        with self.assertRaisesRegex(ValueError, "no common native Python module"):
            select_common_source_path("flask", ["src/flask/old.py"], ["src/flask/new.py"], "src/flask", "src/flask")


if __name__ == "__main__":
    unittest.main(verbosity=2)
