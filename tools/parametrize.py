#!/usr/bin/env python3
"""Turn hard-coded search constants in a Reckless checkout into SPSA-tunable parameters.

Reckless already ships a `spsa` cargo feature and a `define!` macro in src/parameters.rs, but
the master branch does not invoke it. This script rewrites the literals listed in
tunables.json into calls like `crate::parameters::lmr_base()` and appends a `define!{}` block.

Without the `spsa` feature these are `const fn`s, so a normal build is byte-for-byte the same speed.
With `--features spsa` each one becomes a UCI option settable with `setoption`.

usage: parametrize.py RECKLESS_DIR [--values tuned.json]
  --values  JSON {name: value} (output of spsa.py) used as the new defaults ("baking in" a tune)
"""
import json, re, sys, pathlib

def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    root = pathlib.Path(args[0])
    values = {}
    if "--values" in args:
        values = json.load(open(args[args.index("--values") + 1]))
    spec = json.load(open(pathlib.Path(__file__).with_name("tunables.json")))
    target = root / spec["target"]
    src = target.read_text()
    if "crate::parameters::" in src:
        sys.exit("already parametrized (run on a clean checkout)")
    decls = []
    for edit in spec["edits"]:
        pattern = r"\s+".join(re.escape(t) for t in edit["old"].split())
        hits = list(re.finditer(pattern, src))
        if len(hits) != 1:
            sys.exit(f"snippet matched {len(hits)} times (needs 1): {edit['old']}")
        new = edit["new"]
        for prm in edit["params"]:
            new = re.sub(r"@%s\b" % prm["name"], "crate::parameters::%s()" % prm["name"], new)
            val = int(round(values.get(prm["name"], prm["default"])))
            decls.append(f"    i32 {prm['name']}: {val};")
        m = hits[0]
        src = src[: m.start()] + new + src[m.end():]
    target.write_text(src)
    pfile = root / "src/parameters.rs"
    pfile.write_text(pfile.read_text().rstrip() + "\n\ndefine! {\n" + "\n".join(decls) + "\n}\n")
    print(f"parametrized {len(decls)} constants in {spec['target']}")

if __name__ == "__main__":
    main()
