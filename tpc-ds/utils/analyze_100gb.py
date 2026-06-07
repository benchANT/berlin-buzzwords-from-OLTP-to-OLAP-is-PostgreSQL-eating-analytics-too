import re, pathlib

base = pathlib.Path("/mnt/c/git/omi-gitlab/baas/benchmark-results/berlin-buzzwords")

def parse_latency(path, metric="AverageLatency"):
    data = {}
    txt = pathlib.Path(path).read_text(errors="replace")
    pattern = rf'^\[QUERY-(query\d+)\],\s*{metric}\(us\),\s*([\d.E+]+)'
    for m in re.finditer(pattern, txt, re.MULTILINE):
        data[m.group(1)] = float(m.group(2))
    return data

pgd_path = base / "results/tpc-ds-original/100gb/olap_tpc-ds_postgresql-pg_duckdb-100gb-1-thread-sequential-1-iterations_0_3vDNNYJr/0_run.txt"
pg_path  = base / "results/tpc-ds-original/100gb/olap_tpc-ds_postgresql-plain-100gb-1-thread-sequential-1-iterations_0_weWMXyrj/0_run.txt"

pgd = parse_latency(pgd_path)
pg  = parse_latency(pg_path)

DRAW_THRESHOLD = 0.10
queries = sorted(set(pgd.keys()) & set(pg.keys()), key=lambda q: int(q.replace("query","")))

wins = draws = losses = 0

print("TPC-DS 100GB — PostgreSQL + pg_duckdb vs PostgreSQL plain (1 thread, 1 iteration)")
print("=" * 90)
print(f"{'Query':<10} {'pg_duckdb':>14} {'PG plain':>14}  {'Winner':<20} {'Factor':>8}")
print("-" * 90)

for q in queries:
    a = pgd[q]  # pg_duckdb
    b = pg[q]   # plain PG
    ratio = abs(a - b) / max(a, b)

    if ratio <= DRAW_THRESHOLD:
        result = "DRAW"
        draws += 1
        factor = max(a,b)/min(a,b)
        winner_str = f"Draw (within {ratio*100:.1f}%)"
        factor_str = f"~{factor:.2f}x"
    elif a < b:
        result = "pgduckdb"
        wins += 1
        factor = b / a
        winner_str = "pg_duckdb wins"
        factor_str = f"{factor:.2f}x faster"
    else:
        result = "PG plain"
        losses += 1
        factor = a / b
        winner_str = "PG plain wins"
        factor_str = f"{factor:.2f}x faster"

    def fmt(us):
        s = us / 1e6
        if s >= 60:
            return f"{s/60:.1f} min ({s:.0f}s)"
        return f"{s:.1f}s"

    print(f"{q:<10} {fmt(a):>14} {fmt(b):>14}  {winner_str:<20} {factor_str:>14}")

print("-" * 90)
print(f"\nWin/Draw/Loss (pg_duckdb vs PG plain, 10% draw threshold):")
print(f"  pg_duckdb wins: {wins}   Draws: {draws}   PG plain wins: {losses}")
print(f"\nNote: pg_duckdb ran with duckDbForceExecution=false (may fall back to PG executor).")
print(f"      Multiple queries show near-identical latency (~419s), suggesting possible")
print(f"      fallback to PostgreSQL executor for those queries.")
