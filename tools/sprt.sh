#!/usr/bin/env bash
# sprt.sh DEV BASE [tc] - gainer SPRT [0, 2] Elo (normalized), the same bounds OpenBench uses for non-regression/gain.
# A patch is accepted only if this prints "H1 was accepted".
set -euo pipefail
W=${WORK:-work}
DEV=$1; BASE=$2; TC=${3:-8+0.08}
exec "$W/fastchess/fastchess" \
  -engine cmd="$DEV" name=dev option.Hash=16 option.Threads=1 \
  -engine cmd="$BASE" name=base option.Hash=16 option.Threads=1 \
  -each tc="$TC" -rounds 100000 -games 2 -repeat -recover -concurrency "${CONC:-$(nproc)}" \
  -openings file="$W/UHO_Lichess_4852_v1.epd" format=epd order=random \
  -sprt elo0=0 elo1=2 alpha=0.05 beta=0.05 model=normalized -ratinginterval 50
