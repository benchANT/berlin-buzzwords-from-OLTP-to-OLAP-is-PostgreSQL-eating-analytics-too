import re
from pathlib import Path

BASE_DIR = Path("/mnt/c/git/omi-gitlab/baas/benchmark-results/berlin-buzzwords/results/tpc-ds-original/10gb")

ch_path  = BASE_DIR / "olap_tpc-ds_clickhouse-aws-10gb-1-thread-sequential_0_CXr4UXO4/0_run.txt"
pgd_path = BASE_DIR / "olap_tpc-ds_postgresql-pg_duckdb-10gb-1-thread-sequential_0_9QYv4eVb/0_run.txt"
pg_path  = BASE_DIR / "olap_tpc-ds_postgresql-plain-10gb-1-thread-sequential_0_4ivcQAtK/0_run.txt"

_RE = re.compile(r'^\[QUERY-(query\d+)\],\s*95thPercentileLatency\(us\),\s*([0-9.eE+]+)')

QUERY_LABEL_MAP = {
    "query16": "Q03", "query17": "Q07", "query18": "Q19", "query19": "Q42",
    "query20": "Q52", "query21": "Q56", "query22": "Q26", "query23": "Q68",
    "query24": "Q73", "query25": "Q96",
}

def parse(path):
    d = {}
    for line in path.open(errors="replace"):
        m = _RE.match(line.strip())
        if m:
            d[m.group(1)] = float(m.group(2)) / 1e6
    return d

ch  = parse(ch_path)
pgd = parse(pgd_path)
pg  = parse(pg_path)

DRAW = 0.10
queries = sorted(set(ch) & set(pgd) & set(pg), key=lambda s: int(s.replace("query","")))

def cmp(a, b):
    """Return (result_str, factor_str) comparing a vs b."""
    if max(a, b) == 0:
        return "Draw", "—"
    ratio = abs(a - b) / max(a, b)
    if ratio <= DRAW:
        return "Draw", f"within {ratio*100:.1f}%"
    elif a < b:
        return "wins", f"{b/a:.2f}x faster"
    else:
        return "loses", f"{a/b:.2f}x slower"

# --- Per-query overall winner ---
print("TPC-DS 10 GB — P95 Latency (1 thread, 100 iterations)")
print("=" * 85)
print(f"{'Query':<8} {'ClickHouse':>11} {'pg_duckdb':>11} {'PostgreSQL':>11}  {'Overall winner'}")
print("-" * 85)

ch_wins = pgd_wins = pg_wins = draws_all = 0

for q in queries:
    label = QUERY_LABEL_MAP.get(q, q)
    c, a, b = ch[q], pgd[q], pg[q]
    best_val = min(c, a, b)
    # find winner(s) within 10% of best
    threshold = best_val * (1 + DRAW)
    in_draw = [name for name, val in [("ClickHouse", c), ("pg_duckdb", a), ("PostgreSQL", b)]
               if val <= threshold]
    if len(in_draw) > 1:
        winner = "Draw (" + ", ".join(in_draw) + ")"
        draws_all += 1
    elif c == best_val:
        winner = f"ClickHouse  ({min(a,b)/c:.2f}x over next)"
        ch_wins += 1
    elif a == best_val:
        winner = f"pg_duckdb  ({min(c,b)/a:.2f}x over next)"
        pgd_wins += 1
    else:
        winner = f"PostgreSQL  ({min(c,a)/b:.2f}x over next)"
        pg_wins += 1

    print(f"{label:<8} {c:>10.2f}s {a:>10.2f}s {b:>10.2f}s  {winner}")

print("-" * 85)
print(f"\nOverall wins (10% draw threshold):")
print(f"  ClickHouse: {ch_wins}   pg_duckdb: {pgd_wins}   PostgreSQL: {pg_wins}   Multi-way draws: {draws_all}")

# --- Pairwise: pg_duckdb vs PostgreSQL ---
print("\n--- Pairwise: pg_duckdb vs PostgreSQL ---")
w = d = l = 0
for q in queries:
    r, f = cmp(pgd[q], pg[q])
    if r == "wins": w += 1
    elif r == "Draw": d += 1
    else: l += 1
print(f"  pg_duckdb wins: {w}   Draws: {d}   PostgreSQL wins: {l}")

# --- Pairwise: pg_duckdb vs ClickHouse ---
print("\n--- Pairwise: pg_duckdb vs ClickHouse ---")
w = d = l = 0
for q in queries:
    r, f = cmp(pgd[q], ch[q])
    if r == "wins": w += 1
    elif r == "Draw": d += 1
    else: l += 1
print(f"  pg_duckdb wins: {w}   Draws: {d}   ClickHouse wins: {l}")
