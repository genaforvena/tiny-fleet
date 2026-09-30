#!/usr/bin/env python3
import unittest

from build_drift_train_corpus import classify_file, split_paths


class DriftTrainingCorpusTests(unittest.TestCase):
    def test_only_licensed_native_python_files_enter_training(self):
        included, reason = classify_file(
            "src/flask/app.py", "100644", b"class Flask:\n    pass\n",
            package_root="src/flask", license_spdx="BSD-3-Clause", heldout_path="src/flask/cli.py",
        )
        self.assertTrue(included)
        self.assertEqual(reason, "")

    def test_excludes_tests_nonpackage_heldout_and_nonregular_files(self):
        cases = [
            ("tests/test_app.py", "100644", "outside-native-package"),
            ("src/flask/tests/test_app.py", "100644", "test-tree"),
            ("src/flask/test_app.py", "100644", "test-source-file"),
            ("src/flask/cli.py", "100644", "heldout-source-file"),
            ("src/flask/app.py", "120000", "non-regular-file"),
            ("src/flask/app.txt", "100644", "non-python-file"),
        ]
        for path, mode, expected_reason in cases:
            with self.subTest(path=path):
                included, reason = classify_file(
                    path, mode, b"content\n", package_root="src/flask",
                    license_spdx="BSD-3-Clause", heldout_path="src/flask/cli.py",
                )
                self.assertFalse(included)
                self.assertEqual(reason, expected_reason)

    def test_rejects_malformed_or_incompatibly_marked_source(self):
        malformed = classify_file(
            "src/flask/app.py", "100644", b"\xff", package_root="src/flask",
            license_spdx="BSD-3-Clause", heldout_path="src/flask/cli.py",
        )
        incompatible = classify_file(
            "src/flask/app.py", "100644", b"# SPDX-License-Identifier: GPL-3.0-only\n", package_root="src/flask",
            license_spdx="BSD-3-Clause", heldout_path="src/flask/cli.py",
        )
        self.assertEqual(malformed, (False, "malformed-utf8"))
        self.assertEqual(incompatible, (False, "file-license-mismatch"))

    def test_validation_split_is_deterministic_and_disjoint(self):
        paths = [f"src/pkg/file-{index}.py" for index in range(20)]
        train, validation = split_paths("flask", "old", paths, validation_fraction=0.2)
        shuffled_train, shuffled_validation = split_paths("flask", "old", list(reversed(paths)), validation_fraction=0.2)
        self.assertEqual((train, validation), (shuffled_train, shuffled_validation))
        self.assertEqual(len(validation), 4)
        self.assertFalse(set(train) & set(validation))
        self.assertEqual(set(train) | set(validation), set(paths))


if __name__ == "__main__":
    unittest.main(verbosity=2)
