# Haunt receipt: six v2 snapshot adapters trained

Task: `tinyfleet-drift-v2-implementation-20260913/train-six-v2-snapshot-adapters`.

The six snapshot-specific LoRA adapters were trained sequentially with the frozen plan and
license-filtered corpora. The adapter registration is
`runs/drift-generative-v2/adapter-registration.json`, SHA256
`3896fd9fd5df55775caf37fc6432d420ce97658967a8b7a3cce42b2c97671db7`. It pins
`HuggingFaceTB/SmolLM2-360M-Instruct` revision
`a10cc1512eabd3dde888204e902eca88bddb4951`, seed 17, and plan SHA256
`e82978c938be4c51ed8924e18ee1fcc45a51558cecd88cd1e6319c2670ae5c39`.

| Snapshot | Adapter SHA256 | Validation NLL before → after | Optimizer steps |
| --- | --- | ---: | ---: |
| Flask old | `9012ad80a9aacfd95eb30f133fc1d7975e683df58af3bd7230a6c37d69117666` | 1.96384 → 1.91202 | 17 |
| Flask new | `ba7bae9ab2e561fe56765350b8258d11acc10a259a5858f475958b17a3ab47fa` | 1.82940 → 1.77080 | 17 |
| Pydantic old | `987a7880e98bf494869a5edac4a58e906fd60350bdd892f1681708da9c978e85` | 1.79786 → 1.77091 | 17 |
| Pydantic new | `e0e23af43fac2f5001e23c1ee033c76a54ad658b415cf45949679d9c15a1d4bf` | 1.89331 → 1.85366 | 17 |
| Requests old | `fd363d3a8ff887e075ef5d8cbe02fefc46570330ccfbdc2e1b23b69a5627d8a5` | 1.55879 → 1.52926 | 17 |
| Requests new | `d2d388b1fb4f996edf797019d0245b79ec519a020df15c5ab6868ddea07f45f6` | 2.04141 → 2.00128 | 17 |

Every `run.json` records `status=complete`, `mesh-heavy-run` return code 0, the adapter file
hashes, corpus and validation manifest hashes, training runtime, resource observations, and a
passing restoration check. An independent local check recomputed all six adapter tree digests,
each referenced run-manifest digest and adapter-file digest, and verified the registration's
corpus references and finite, decreased validation losses. `mesh-gpu-lease --status` returned
`GPU_LEASE=none`; the three managed services (`mesh-voice-clone`, `mesh-room-gigaam`, `ollama`)
were active again, matching the recorded pre-lease state.

Validation performed: `python3 scripts/test_build_drift_train_corpus.py` (4/4) and
`python3 scripts/test_train_drift_adapters.py` (3/3); both passed. The saved validation NLL is
file-disjoint adaptation diagnostics only and says nothing about semantic correctness on the
held-out excerpts.

The preflight temporal limitation remains: objective labels and a generic model smoke preceded
held-out excerpt selection. The current sample is therefore exploratory/implementation-audit only;
confirmation still requires an unseen sample or independent review. Do not resume the original
analysis until the independent D04 label and v2 execution-artifact gates pass.
