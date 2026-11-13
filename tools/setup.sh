#!/usr/bin/env bash
# Fetches everything needed to test Reckless against Stockfish locally (Linux x86-64).
# Needs: git, curl, unzip, g++, make, python3, rustup (https://rustup.rs)
set -euo pipefail
W=${1:-work}; mkdir -p "$W"; cd "$W"
[ -d reckless ]   || git clone --depth 1 https://github.com/codedeliveryservice/Reckless.git reckless
[ -d fastchess ]  || git clone --depth 1 https://github.com/Disservin/fastchess.git fastchess
[ -x fastchess/fastchess ] || make -C fastchess -j"$(nproc)"
if [ ! -x sf-latest ]; then
  TAG=${SF_TAG:-sf_19}
  # universal build works on any x86-64 CPU
  curl -sfL "https://github.com/official-stockfish/Stockfish/releases/download/$TAG/stockfish-linux-x86-64-universal.tar.gz" -o sf.tgz \
    && tar xzf sf.tgz && cp stockfish/stockfish-linux-x86-64-universal sf-latest
fi
[ -f UHO_Lichess_4852_v1.epd ] || { curl -sL https://github.com/official-stockfish/books/raw/master/UHO_Lichess_4852_v1.epd.zip -o book.zip && unzip -oq book.zip; }
echo "ready in $W/"
