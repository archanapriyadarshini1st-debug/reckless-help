#!/usr/bin/env python3
"""SPSA tuner for Reckless (built with --features spsa), driven by fastchess. Stdlib only.

Each iteration:
  1. draw a random +/-1 vector delta
  2. theta+ = clip(theta + c_i*delta), theta- = clip(theta - c_i*delta)
  3. play a paired-opening match theta+ vs theta- with the same binary
  4. result r = (W - L) / games   (in [-1, 1])
  5. theta += a_k * c_i * delta * r          (ascent on score)
Gain a_k and perturbation c_k decay as in Spall's schedules. Progress is checkpointed
to --state every iteration so runs are resumable (important on CI / spot machines).

usage: spsa.py --engine ./reckless-spsa --book book.epd --iterations 2000
"""
import argparse, json, math, os, random, re, subprocess, sys, time

SCORE = re.compile(r"Results of plus vs minus.*?Games: (\d+), Wins: (\d+), Losses: (\d+), Draws: (\d+)", re.S)

def load_params(path):
    spec = json.load(open(path))
    out = {}
    for e in spec["edits"]:
        for p in e["params"]:
            out[p["name"]] = p
    return out

def play(a, args, plus, minus, seed):
    cmd = [args.fastchess,
           "-engine", f"cmd={args.engine}", "name=plus", f"option.Hash={args.hash}", "option.Threads=1",
           *[f"option.{k}={int(round(v))}" for k, v in plus.items()],
           "-engine", f"cmd={args.engine}", "name=minus", f"option.Hash={args.hash}", "option.Threads=1",
           *[f"option.{k}={int(round(v))}" for k, v in minus.items()],
           "-each", f"tc={args.tc}", "-rounds", str(args.pairs), "-games", "2", "-repeat",
           "-concurrency", str(args.concurrency), "-recover",
           "-openings", f"file={args.book}", "format=epd", "order=random", f"-srand", str(seed),
           "-ratinginterval", "0"]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    m = SCORE.findall(out)
    if not m:
        raise RuntimeError("could not parse fastchess output:\n" + out[-800:])
    _, w, l, d = (int(x) for x in m[-1])
    return w, l, d

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True)
    ap.add_argument("--fastchess", default="fastchess")
    ap.add_argument("--book", required=True)
    ap.add_argument("--tunables", default=os.path.join(os.path.dirname(__file__), "tunables.json"))
    ap.add_argument("--iterations", type=int, default=1000)
    ap.add_argument("--pairs", type=int, default=8, help="game pairs per iteration")
    ap.add_argument("--tc", default="5+0.05")
    ap.add_argument("--hash", type=int, default=16)
    ap.add_argument("--concurrency", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--a", type=float, default=0.6, help="initial gain (fraction of step per unit score)")
    ap.add_argument("--A-frac", type=float, default=0.1, help="stability constant as fraction of iterations")
    ap.add_argument("--alpha", type=float, default=0.602)
    ap.add_argument("--gamma", type=float, default=0.101)
    ap.add_argument("--state", default="spsa-state.json")
    ap.add_argument("--out", default="tuned.json")
    ap.add_argument("--only", default="", help="comma-separated subset of parameter names (e.g. lmr_)", )
    args = ap.parse_args()

    P = load_params(args.tunables)
    if args.only:
        pref = args.only.split(",")
        P = {k: v for k, v in P.items() if any(k.startswith(x) for x in pref)}
    if os.path.exists(args.state):
        st = json.load(open(args.state))
        theta, k0 = st["theta"], st["iter"]
        print(f"resuming at iteration {k0}")
    else:
        theta, k0 = {n: float(p["default"]) for n, p in P.items()}, 0
    A = args.A_frac * args.iterations
    rng = random.Random(1234)
    for _ in range(k0): rng.random()
    tot = [0, 0, 0]
    for k in range(k0, args.iterations):
        ak = args.a / (A + k + 1) ** args.alpha * (A + 1) ** args.alpha
        ck = 1.0 / (k + 1) ** args.gamma
        delta = {n: rng.choice((-1, 1)) for n in P}
        plus, minus = {}, {}
        for n, p in P.items():
            c = max(p["step"] * ck, 1.0)
            plus[n] = min(max(theta[n] + c * delta[n], p["min"]), p["max"])
            minus[n] = min(max(theta[n] - c * delta[n], p["min"]), p["max"])
        w, l, d = play(k, args, plus, minus, seed=k + 1)
        g = w + l + d
        r = (w - l) / g if g else 0.0
        for n, p in P.items():
            c = max(p["step"] * ck, 1.0)
            theta[n] = min(max(theta[n] + ak * c * delta[n] * r, p["min"]), p["max"])
        for i, v in enumerate((w, l, d)): tot[i] += v
        json.dump({"theta": theta, "iter": k + 1}, open(args.state, "w"))
        json.dump({n: int(round(v)) for n, v in theta.items()}, open(args.out, "w"), indent=1)
        print(f"[{k+1}/{args.iterations}] +{w} -{l} ={d}  a_k={ak:.3f} c_k={ck:.3f}", flush=True)

if __name__ == "__main__":
    main()
