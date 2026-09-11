# D04 drift-validation registration

Status: registered fixture; external comparison remains preliminary.
Registered: 2026-09-11 UTC
Owner: haunt

## Claim and estimands

This run asks whether structural, lexical, generative, and behavioral drift
metrics agree with independently observed changes between two immutable
repository snapshots. The four estimands remain separate; no aggregate drift
score is registered.

## Frozen labels

The label vocabulary is `no_change`, `cosmetic`, `interface_change`,
`dependency_change`, and `behavior_change`. A unit may receive an architectural
label only when its frozen evidence is a release note, commit diff, or native
test. Cosmetic and no-change units are explicit negative examples and cannot be
promoted by a metric. Each main unit has two distinct blinded reviewers;
disagreements require a recorded adjudication.

The fixture uses three independent repository identities and immutable commit
IDs in `runs/drift-validation-v1/registration.json`. The previously attempted
external-repository freeze is not a valid three-repository freeze, so this
registration does not claim external generalisation or a measured association.
The run is deliberately `preliminary` until an independent freeze supplies
source manifests and the D04-V review approves the registration.

## Blinding and leakage controls

`score_reveal` is false. Labels contain evidence only; model scores, drift
predictions, and generated outputs are forbidden in the label file. The
validator rejects leaked score fields, duplicate units, unregistered repos,
missing reviewers, unresolved disagreements, and architectural labels attached
to cosmetic/no-change units.

## Required next action

Run `rtk proxy .venv/bin/python scripts/test_drift_validate.py`, then have vpn
verify this commit in an isolated checkout with a mutation and an independent
negative case. Only after that review may the separate external comparison task
reveal scores. This artifact does not unlock `run-paired-replications`.
