#!/usr/bin/env bash
# build.sh DIR  ->  DIR/reckless-base (stock) and DIR/reckless-spsa (tunable) binaries
# Builds without syzygy so no clang is needed; tablebases don't matter for self-play tuning.
set -euo pipefail
W=${1:-work}; here=$(cd "$(dirname "$0")" && pwd)
export RUSTFLAGS="${RUSTFLAGS:--C target-cpu=native}"
cd "$W/reckless"; git checkout -q . ; git clean -fdq src
cargo build --release --no-default-features && cp target/release/reckless ../reckless-base
python3 "$here/parametrize.py" . ${VALUES:+--values "$VALUES"}
cargo build --release --no-default-features --features spsa && cp target/release/reckless ../reckless-spsa
git checkout -q . 
echo "built reckless-base and reckless-spsa"
