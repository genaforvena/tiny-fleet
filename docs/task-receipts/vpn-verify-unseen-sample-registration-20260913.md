# Independent registration audit — 2026-09-13

Task: `tinyfleet-drift-confirmatory-prerequisites-20260913/verify-unseen-sample-registration`
Auditor: `vpn`
Registration: `runs/drift-confirmatory-v1/registration.json`

## Verdict

**PASS, bounded to the recorded study materials and event trail.** I found no mismatch in the
replacement sample's pinned source, license, selection, label, or preservation hashes. Its three
repositories and six commits are disjoint from the recorded prior inference sample and adapter
training corpus. The objective labels follow metadata-only selection and snapshot retrieval, and
the available run artifacts contain no inference or comparison result for this sample. This audit
does not claim that the base model's unknown pretraining corpus excludes these repositories or
that an inference outside the recorded study trail is metaphysically impossible.

The live ledger check showed this exact step open and assigned to `vpn`; step 0 was done with
`docs/task-receipts/haunt-freeze-unseen-confirmatory-sample-20260913.md` as its artifact. The
current tiny-fleet checkout has the freeze files clean at commit
`d7feb0ef5a8dc928319c06fe89b543383b604a3f` (`Freeze unseen drift confirmatory sample`).

## Evidence

- **Pinned source — PASS.** Current GitHub tag refs resolve to the registered commits: HTTPX
  `0.23.1` → `f11eff45…` and `0.28.1` → `26d48e06…`; attrs `22.2.0` →
  `a9960de9…` and `24.3.0` → `598494a6…`; pytest `7.2.0` → `3af3f569…` and
  `8.3.4` → `53f8b4e6…`. I independently ran `git archive --format=tar <commit>` from the
  retained bare clones for all six commits; each output SHA-256 exactly matched its registered
  archive hash. Repository metadata records canonical, non-fork, non-archived upstreams.
- **License provenance — PASS.** The recorded GitHub SPDX values are BSD-3-Clause for HTTPX and
  MIT for attrs and pytest. The verifier checked each license copy against the license member in
  both pinned archives. The six license-copy hashes also match the registration.
- **Disjointness — PASS for recorded material.** New repo IDs are `httpx`, `attrs`, and `pytest`.
  Prior v2 inference/sample IDs are `flask`, `requests`, and `pydantic`; v1 was explicitly
  fixture-only (`ripgrep`, `fd`, `jq`). All six adapter-training records name only flask,
  requests, or pydantic. There is no repository or commit intersection. The registration itself
  limits this conclusion to recorded study material, not unknown base-model pretraining.
- **Score-blind chronology — PASS.** Re-running
  `scripts/select_drift_confirmatory_snapshots.py` on the retained metadata clones reproduced
  `selection.json` byte-for-byte. The selector reads stable-tag and commit metadata only; its
  fixed anchors are 2023-01-01 and 2025-01-01. `access-chronology.jsonl` records the selection
  frozen at 16:11:52Z, the six source archives created from 16:13:17Z through 16:13:20Z, and
  objective evidence review/label write at 16:21:10Z. The labels contain three narrow public
  interface changes tied to pinned old/new source/export files and new-snapshot release notes;
  no score, test result, or model output is a label input. The chronology file's SHA-256 is
  `298b02d42691845976d3e96fcbc73a6479bb0d81b83bdb900ea4a400b007d397` and it is committed
  alongside registration at the freeze commit. Note: registration records the chronology path
  and rule but does not itself carry the chronology file hash.
- **Hashes and preserved registration — PASS.**
  `scripts/verify_drift_confirmatory_freeze.py` passed, validating all six archive byte counts and
  hashes; all six license-copy/member hashes; label source, public-export, test-source, and release
  note hashes; selection/code/repository-metadata hashes; and the four unchanged prior-registration
  hashes. Independently recomputed hashes: registration
  `f21f4b9afcce8146d4f67cc78c0f1041bcd467676ac3a5aad812476a6cbc60e8`, selection
  `a50a3a8e288188d930e6432704a7414dbb0f8acaf4eca37460e828775c696a30`, labels
  `8bbb3047ebe375d5d0077e563b72d6d74578dfb21e1805fb6df1865038aeb5db`, selector code
  `b8b286e3e47ab0dcad2130afcc8f77f85889693c055b31303222bbf0dad7a3d6`.
- **No-inference claim — PASS within available records.** Registration says comparison and model
  scores are unauthorized. Chronology records no inference, backend/embedding smoke, scorer, test
  smoke, or comparison before freeze. The confirmatory run directory has only frozen inputs,
  provenance, labels, and registration; it has no output, result, or run-manifest artifacts. The
  separate task/board state keeps behavioral gates and comparison authorization pending. This is
  evidence for the recorded workflow, not a proof about unlogged external activity.

## Verification and next gate

Commands: live `mesh-task status`; current `git ls-remote` checks for all six upstream tags;
six local `git archive` hash comparisons; metadata-selector rerun plus byte comparison; and
`python3 scripts/verify_drift_confirmatory_freeze.py` (PASS).

No edits were made to the frozen registration or sample. Comparison remains unauthorized. The next
step is `resolve-behavioral-snapshot-gates`; independent behavioral verification and the final gate
remain open.
