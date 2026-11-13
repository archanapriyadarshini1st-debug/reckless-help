#!/usr/bin/env bash
# match.sh ENGINE_A ENGINE_B [rounds] [tc]   - head-to-head, prints score + Elo with error bars
set -euo pipefail
W=${WORK:-work}
A=$1; B=$2; R=${3:-250}; TC=${4:-8+0.08}
exec "$W/fastchess/fastchess" \
  -engine cmd="$A" name=A option.Hash=16 option.Threads=1 \
  -engine cmd="$B" name=B option.Hash=16 option.Threads=1 \
  -each tc="$TC" -rounds "$R" -games 2 -repeat -recover -concurrency "${CONC:-$(nproc)}" \
  -openings file="$W/UHO_Lichess_4852_v1.epd" format=epd order=random -ratinginterval 20
