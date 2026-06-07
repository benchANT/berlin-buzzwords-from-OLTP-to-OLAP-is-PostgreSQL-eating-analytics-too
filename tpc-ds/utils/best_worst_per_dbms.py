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

systems = {
    "ClickHouse":  ch,
    "pg_duckdb":   pgd,
    "PostgreSQL":  pg,
}

for name, own in systems.items():
    others = {k: v for k, v in systems.items() if k != name}
    best_q = worst_q = None
    best_factor = 0
    worst_factor = 0

    for q in queries:
        label = QUERY_LABEL_MAP.get(q, q)
        own_val = own[q]
        other_vals = [v[q] for v in others.values()]
        best_other = min(other_vals)   # fastest competitor
        worst_other = max(other_vals)  # slowest competitor

        # "best" for this DBMS = biggest factor where it beats ALL others
        if own_val < best_other:
            factor = best_other / own_val
            if factor > best_factor:
                best_factor = factor
                best_q = (label, own_val, {k: v[q] for k,v in others.items()}, factor)

        # "worst" = biggest factor where it's slower than ALL others
        if own_val > worst_other:
            factor = own_val / worst_other
            if factor > worst_factor:
                worst_factor = factor
                worst_q = (label, own_val, {k: v[q] for k,v in others.items()}, factor)

    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    if best_q:
        label, own_val, others_d, factor = best_q
        others_str = "  ".join(f"{k}={v:.2f}s" for k,v in others_d.items())
        print(f"  BEST  {label}: {own_val:.2f}s  vs  {others_str}")
        print(f"         → {factor:.2f}x faster than closest competitor")
    else:
        print("  BEST: no query where it beats all others outright")

    if worst_q:
        label, own_val, others_d, factor = worst_q
        others_str = "  ".join(f"{k}={v:.2f}s" for k,v in others_d.items())
        print(f"  WORST {label}: {own_val:.2f}s  vs  {others_str}")
        print(f"         → {factor:.2f}x slower than fastest competitor")
    else:
        print("  WORST: no query where it loses to all others outright")
