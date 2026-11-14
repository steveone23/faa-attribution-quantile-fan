"""Check forecast outputs against the bounty's shape rules.

Usage: python validate.py <input_dir> <output_dir>

For every <id>.in in input_dir, <id>.out in output_dir must be JSON with exactly
one key "forecasts", one entry per market id of the case and no other, each with
horizon_minutes rows of 5 finite numbers in [0, 1] that are non-decreasing, and
the file must be at most 1,048,576 bytes. Exits non-zero on any failure.
"""

import json
import math
import os
import sys

MAX_BYTES = 1048576
N_QUANTILES = 5


def is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def check_case(in_path, out_path):
    """Return a list of error strings for one case."""
    errors = []
    with open(in_path, "r", encoding="utf-8") as fh:
        case = json.load(fh)
    horizon = case.get("horizon_minutes", 240)
    ids = [m.get("id") for m in case.get("markets", [])]

    if not os.path.isfile(out_path):
        return ["missing output file"]
    size = os.path.getsize(out_path)
    if size > MAX_BYTES:
        errors.append("output is %d bytes, over %d" % (size, MAX_BYTES))
    try:
        with open(out_path, "r", encoding="utf-8") as fh:
            out = json.load(fh)
    except Exception as exc:
        return errors + ["invalid JSON: %s" % exc]

    if not isinstance(out, dict) or list(out.keys()) != ["forecasts"]:
        return errors + ["top level must be an object with exactly one key 'forecasts'"]
    forecasts = out["forecasts"]
    if not isinstance(forecasts, list):
        return errors + ["'forecasts' must be a list"]

    seen = []
    for k, entry in enumerate(forecasts):
        if not isinstance(entry, dict) or "id" not in entry or "q" not in entry:
            errors.append("forecast %d must have 'id' and 'q'" % k)
            continue
        mid = entry["id"]
        seen.append(mid)
        q = entry["q"]
        if not isinstance(q, list) or len(q) != horizon:
            errors.append("market %s: expected %d rows" % (mid, horizon))
            continue
        for r, row in enumerate(q):
            if not isinstance(row, list) or len(row) != N_QUANTILES:
                errors.append("market %s row %d: expected %d values" % (mid, r, N_QUANTILES))
                break
            if not all(is_number(v) and 0.0 <= v <= 1.0 for v in row):
                errors.append("market %s row %d: values must be finite and in [0, 1]" % (mid, r))
                break
            if any(row[i] > row[i + 1] for i in range(N_QUANTILES - 1)):
                errors.append("market %s row %d: row is decreasing" % (mid, r))
                break

    if sorted(map(str, seen)) != sorted(map(str, ids)) or len(set(map(str, seen))) != len(seen):
        errors.append("forecast ids do not match the case's market ids one to one")
    return errors


def main(argv):
    if len(argv) != 3:
        print("usage: python validate.py <input_dir> <output_dir>", file=sys.stderr)
        return 2
    in_dir, out_dir = argv[1], argv[2]
    names = sorted(f for f in os.listdir(in_dir) if f.endswith(".in"))
    if not names:
        print("no .in files in %s" % in_dir, file=sys.stderr)
        return 1
    failed = 0
    for name in names:
        case_id = name[:-3]
        try:
            errors = check_case(os.path.join(in_dir, name), os.path.join(out_dir, case_id + ".out"))
        except Exception as exc:
            errors = ["could not check: %s" % exc]
        if errors:
            failed += 1
            for e in errors:
                print("%s: FAIL %s" % (case_id, e))
        else:
            print("%s: ok" % case_id)
    print("%d of %d cases valid" % (len(names) - failed, len(names)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
