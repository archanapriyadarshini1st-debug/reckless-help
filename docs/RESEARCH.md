# How Reckless and Stockfish get stronger (and what we can do about it)

Both engines are improved by the **same loop**: propose a change -> play thousands of games against the
current master at very fast time controls -> keep it only if a sequential probability ratio test (SPRT)
says it gains. Nothing is merged on intuition.

| | Stockfish | Reckless |
|---|---|---|
| Test framework | Fishtest (volunteer CPU network, millions of games/day) | OpenBench instance |
| Acceptance | SPRT, STC then LTC (and SMP) | SPRT, STC then LTC |
| Eval | NNUE, trained on billions of self-play positions (Leela-derived data), nets updated regularly | NNUE with threat inputs, own net series (`RecklessNetworks`) trained on its own self-play data |
| Param tuning | SPSA on Fishtest, tens of thousands of games per run | SPSA on OpenBench; `spsa` cargo feature + `define!` macro |

## Where the Elo comes from (rough order of impact)

1. **Network quality / training data.** Largest single lever. Needs GPUs and a big data pipeline
   (bullet trainer for Reckless-style nets). Tuning search constants can't compensate for a weaker net.
2. **Search heuristics** — all are parameterised formulas that SPSA can tune:
   * Late-move reductions (LMR): base, history, improving, correction-history, TT-based terms.
   * Pruning: razoring, reverse futility, late-move pruning, SEE pruning, probcut, null-move.
   * Extensions: singular extensions, double/negative extensions.
   * Correction history (pawn / non-pawn / continuation) – used by both engines to correct static eval.
   * Move ordering histories (butterfly, continuation, capture, pawn-history).
3. **Time management** (node-fraction based stability, falling-eval factors).
4. **Multithreading** (Lazy SMP details) and TT replacement policy.
5. **Speed**: NNUE SIMD kernels, incremental accumulator updates, PGO builds (`make pgo`).

## What this repo automates

* `tools/tunables.json` – 35 search constants (razoring, RFP, LMP, SEE, correction-history, LMR) with sane ranges and step sizes.
* `tools/parametrize.py` – rewrites those literals into `crate::parameters::name()` calls. **Verified behaviour-neutral:**
  bench node count is identical (2,837,905) before/after on Reckless 0.10.0-dev.
* `tools/spsa.py` – resumable SPSA tuner on fastchess; `tools/sprt.sh` – the gatekeeper test.
* `.github/workflows/tune.yml` – runs tuning on GitHub runners, uploads `tuned.json`.

## Honest limits

* An SPSA run needs on the order of **20k–100k+ games per ~35 parameters** to move Elo measurably; typical
  gains from retuning an already-tuned engine are **+1 to +5 Elo**, not +50.
* Reckless is already in the same strength class as Stockfish at standard testing conditions; the gap that remains
  (in either direction, depending on book/hardware/TC) is **a few tens of Elo at most** and is dominated by net
  quality, which tuning cannot fix.
* Any claim of "reached Stockfish level" must come from a large match (thousands of games, error bar < ±5 Elo)
  with the exact binaries/net/hardware stated. Use `tools/match.sh`.

## Next experiments (ordered by expected value per CPU-hour)

1. Tune `lmr_*` (12 params) – LMR is the most impactful search formula.
2. Tune `rfp_*`, `lmp_*`, `seeq_*`/`seec_*`.
3. Add new tunables: null-move reduction, singular-extension margins, aspiration window, time-management factors.
4. Add new heuristics from Stockfish and test via SPRT: e.g. extra correction-history terms, tuned continuation history weights.
5. Network: retrain on more data / longer schedule (needs GPU; out of scope for this repo's CI).
