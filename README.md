# reckless-help

Tuning, testing and research workbench for the [Reckless](https://github.com/codedeliveryservice/Reckless) chess engine.
Goal: close the gap to Stockfish — **measured with SPRT/matches, never assumed.**

## Status (measured, not claimed)

| Test | Result |
|---|---|
| Parametrization of 35 search constants | bench nodes identical before/after: **2,837,905** |
| Reckless 0.10.0-dev (stock) vs **Stockfish 19**, 150 games, 3+0.03, 1 thread, 16 MB, UHO_Lichess_4852_v1 | **+21 −57 =72 → 38.0 %, ≈ −85 ± 28 Elo** |

So: in this setup (tiny sandbox, very fast TC, no tablebases, short hash) stock Reckless is **still clearly behind SF19**.
That is the number to beat. No tuned build has been shown to improve on it yet — a tuning run needs tens of thousands of games,
which is what the GitHub Actions workflow is for.
Caveat: 150 games at 3+0.03 on a shared 4-core box is a noisy, not a rating-list quality, measurement. Re-measure on your hardware with `tools/match.sh`.

## Quick start

```bash
bash tools/setup.sh work        # clone Reckless + fastchess, fetch Stockfish 19 + opening book
bash tools/build.sh work        # work/reckless-base (stock) and work/reckless-spsa (35 tunable UCI options)

# baseline vs Stockfish
WORK=work bash tools/match.sh work/reckless-base work/sf-latest 500 8+0.08

# tune (resumable; --only takes name prefixes)
python3 tools/spsa.py --engine work/reckless-spsa --fastchess work/fastchess/fastchess \
    --book work/UHO_Lichess_4852_v1.epd --iterations 2000 --pairs 16 --only lmr_

# bake tuned values in as defaults: work/reckless-spsa is then the tuned engine, work/reckless-base stays stock
VALUES=$PWD/tuned.json bash tools/build.sh work
WORK=work bash tools/sprt.sh work/reckless-spsa work/reckless-base   # ship only if "H1 was accepted"
```

Run the tuner on CI: **Actions → SPSA tune → Run workflow**.

## Layout

* `tools/tunables.json` – the tunable list (ranges, step sizes). Add more entries to tune more.
* `tools/parametrize.py` – rewrites literals in `src/search.rs` into `crate::parameters::*()` + `define!{}`.
* `tools/spsa.py` – SPSA tuner on fastchess. `tools/sprt.sh` – acceptance test. `tools/match.sh` – head-to-head.
* `docs/RESEARCH.md` – how Reckless/Stockfish improve and what's realistic.

## Licensing

Reckless is AGPL-3.0. This repo only contains tooling and does not redistribute Reckless, Stockfish or their networks.
