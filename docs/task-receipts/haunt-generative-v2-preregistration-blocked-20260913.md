# V2 generative preregistration — exact runtime gap

- Actor: `haunt`
- Task: `tinyfleet-drift-prerequisites-20260913/register-v2-generative-run`
- Checked: `2026-09-13` UTC
- Result: **BLOCKED before generation; partial preregistration frozen**

## Frozen choices

`runs/drift-generative-v2/registration.json` binds the exact v2 sample hash and all six commit
pairs, the base checkpoint `HuggingFaceTB/SmolLM2-360M-Instruct` at immutable revision
`a10cc1512eabd3dde888204e902eca88bddb4951`, the prompt template and arm input contract, decoding
(`temperature=0.7`, `top_p=0.9`, 128 new tokens), seeds `17,29,43`, repetitions `0,1,2`, and the
candidate `all-minilm:latest` embedding model digest. It does not claim the six effective prompts,
LoRA adapters, scorer implementation, or outputs are complete. No output or score was generated.

## Exact blockers and retry

The verified D03 interface uses `FakeBackend` from its CLI and serializes one prompt and one model
digest across all arms, without adapter digests. It cannot encode the registered base-only,
snapshot-context, and six snapshot-specific LoRA inputs. Existing LoRA artifacts are trained for
unrelated tasks and are excluded. The six held-out excerpts and a deterministic scoring
implementation are also not yet pinned.

Retry after (1) D03 records effective input, model revision, and adapter digest per row and has an
independently verified real backend; (2) six per-snapshot adapters are trained from the frozen
license-filtered corpora; (3) the six held-out excerpts are hashed before inference; and (4) a
deterministic scorer implementation is committed and pinned. Then run the complete 162-record
matrix. Until all four conditions have evidence, generative remains blocked and no comparison may
be recovered.

## Verification

- `python3 -m json.tool runs/drift-generative-v2/registration.json` — exit 0.
- Sample manifest binding assertion — exit 0; SHA-256 `07c2b0b34f204b2ef549ecf1aa7c581fb7c03af1dbcb8e4a9b4581d392b3ee59`.
- `.venv/bin/python scripts/test_drift_generate.py` — exit 0; 3 tests passed.
- Runtime inventory: cached SmolLM2 revision and PEFT training stack present; unrelated adapters
  excluded. No production inference or scoring process started.
- `registration.json` SHA-256 `df8c67e0c2f4dd31fc673b8af1438d6c3496f79d90a436521b945a304d44fe02`.
- `environment.txt` SHA-256 `4bf04a6c879bcee5cc309a926e0fe3611dfbe572e29940335d9081045a0df4e5`.
- `decision.md` SHA-256 `23a08e5f2f10ab85e77965cb006fa98a6b617f2dea9dfa93766a3342bef1201b`.
