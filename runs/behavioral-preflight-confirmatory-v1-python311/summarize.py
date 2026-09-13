#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REGISTRATION = Path("/home/mesh-home/tiny-fleet/runs/drift-confirmatory-v1/registration.json")

def digest(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

registration = json.loads(REGISTRATION.read_text())
image = "python@sha256:86adf8dbadc3d6e82ee5dd2c74bec2e1c2467cdad47886280501df722372d2e1"
results = {
    "schema": "tiny-fleet.behavioral-preflight-confirmatory-v1/v1",
    "sample_registration": "runs/drift-confirmatory-v1/registration.json",
    "sample_registration_sha256": digest(REGISTRATION),
    "runtime_image": image,
    "platform": "linux/amd64",
    "test_command": "python -m pytest -q",
    "interpretation": "Paired behavioral compatibility preflight only. No comparison, label, model inference, or score is produced.",
    "snapshots": [],
}
for repo in registration["repositories"]:
    for snapshot in repo["snapshots"]:
        name = f"{repo['repo_id']}-{snapshot['label']}"
        outcome_path = HERE / "outcomes" / f"{name}.json"
        outcome = json.loads(outcome_path.read_text()) if outcome_path.exists() else {
            "snapshot": name, "install_exit": None, "test_command": "python -m pytest -q", "test_exit": None
        }
        archive = Path("/home/mesh-home/tiny-fleet") / snapshot["archive"]
        install_log = HERE / "install" / f"{name}.log"
        test_log = HERE / "pytest" / f"{name}.log"
        freeze = HERE / "environments" / f"{name}.freeze.txt"
        outcome.update({
            "repo_id": repo["repo_id"], "label": snapshot["label"], "commit": snapshot["commit"],
            "source_archive": snapshot["archive"], "registered_archive_sha256": snapshot["archive_sha256"],
            "observed_archive_sha256": digest(archive), "runtime_file_sha256": digest(HERE / "environments" / f"{name}.runtime.txt"),
            "install_log_sha256": digest(install_log), "pytest_log_sha256": digest(test_log),
            "environment_freeze_sha256": digest(freeze),
        })
        outcome["verdict"] = (
            "BLOCKED-SETUP" if outcome.get("install_exit") != 0 else
            "PASS" if outcome.get("test_exit") == 0 else
            "BLOCKED-TEST" if outcome.get("test_exit") not in (None, 0) else
            "INCOMPLETE"
        )
        outcome["initial_verdict"] = outcome["verdict"]
        retry_outcome_path = HERE / "retries" / "outcomes" / f"{name}.json"
        if retry_outcome_path.exists():
            retry = json.loads(retry_outcome_path.read_text())
            retry["outcome_sha256"] = digest(retry_outcome_path)
            retry["pytest_log_sha256"] = digest(HERE / "retries" / "pytest" / f"{name}.log")
            retry["environment_freeze_sha256"] = digest(HERE / "retries" / "environments" / f"{name}.freeze.txt")
            retry["install_log_sha256"] = digest(HERE / "retries" / "install" / f"{name}.log")
            outcome["retry"] = retry
            outcome["verdict"] = (
                "BLOCKED-SETUP" if retry.get("install_exit") not in (None, 0) else
                "PASS" if retry.get("test_exit") == 0 else
                "BLOCKED-TEST" if retry.get("test_exit") not in (None, 0) else
                "INCOMPLETE"
            )
        results["snapshots"].append(outcome)
(HERE / "results.json").write_text(json.dumps(results, indent=2) + "\n")
