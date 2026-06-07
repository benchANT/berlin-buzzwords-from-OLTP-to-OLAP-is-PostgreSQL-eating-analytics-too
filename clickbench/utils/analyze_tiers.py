import re
from pathlib import Path

BASE_DIR = Path("/mnt/c/git/omi-gitlab/baas/benchmark-results/berlin-buzzwords/results/clickbench/query")

pgd_path = BASE_DIR / "olap_clickbench_postgresql-indexed-pgduckdb-run-1-iteration_0_9nU9BIvR/0_run.txt"
pg_path  = BASE_DIR / "olap_clickbench_postgresql-indexed-plain-run-1-iteration_0_NhuERdJ8/0_run.txt"

_RE = re.compile(r'^\[QUERY-(query\d+)\],\s*95thPercentileLatency\(us\),\s*([0-9.eE+]+)')

def parse(path):
    d = {}
    for line in path.open(errors="replace"):
        m = _RE.match(line.strip())
        if m:
            d[m.group(1)] = float(m.group(2)) / 1e6  # seconds
    return d

pgd = parse(pgd_path)
pg  = parse(pg_path)

DRAW = 0.10
FAST_MAX = 15
MEDIUM_MAX = 150

all_queries = sorted(set(pgd) | set(pg), key=lambda s: int(s.replace("query","")))

tiers = {"Fast (<15s)": [], "Medium (15–150s)": [], "Heavy (≥150s)": []}
for q in all_queries:
    mx = max(pgd.get(q,0), pg.get(q,0))
    if mx < FAST_MAX:
        tiers["Fast (<15s)"].append(q)
    elif mx < MEDIUM_MAX:
        tiers["Medium (15–150s)"].append(q)
    else:
        tiers["Heavy (≥150s)"].append(q)

DRAW_THRESHOLD = 0.10

for tier, queries in tiers.items():
    results = []
    for q in queries:
        a = pgd.get(q, 0)
        b = pg.get(q, 0)
        if max(a,b) == 0:
            continue
        ratio = abs(a-b)/max(a,b)
        if ratio <= DRAW_THRESHOLD:
            outcome = "DRAW"
            factor = 1.0
        elif a < b:
            outcome = "pgduckdb_wins"
            factor = b/a  # positive = faster
        else:
            outcome = "pg_wins"
            factor = a/b  # positive = faster for pg / regression for pgduckdb

        results.append((q, a, b, outcome, factor, ratio))

    # Best for pgduckdb = largest factor where pgduckdb wins
    wins   = [(q,a,b,f) for q,a,b,o,f,r in results if o == "pgduckdb_wins"]
    losses = [(q,a,b,f) for q,a,b,o,f,r in results if o == "pg_wins"]

    wins_sorted   = sorted(wins,   key=lambda x: -x[3])
    losses_sorted = sorted(losses, key=lambda x: -x[3])

    print(f"\n{'='*70}")
    print(f"Tier: {tier}  ({len(queries)} queries)")
    print(f"{'='*70}")

    print(f"\n  Best 2 for pg_duckdb (biggest speedup over PG plain):")
    for row in wins_sorted[:2]:
        q, a, b, f = row
        print(f"    {q:>8}: pgduckdb={a:.2f}s  PG={b:.2f}s  → {f:.2f}x faster")
    if not wins_sorted:
        print("    (no wins)")

    print(f"\n  Worst 2 for pg_duckdb (biggest regression vs PG plain):")
    for row in losses_sorted[:2]:
        q, a, b, f = row
        print(f"    {q:>8}: pgduckdb={a:.2f}s  PG={b:.2f}s  → {f:.2f}x slower")
    if not losses_sorted:
        print("    (no losses)")
