"""
Grouped bar chart comparing P95 latency per query across three ClickBench datasets.

Datasets:
  - ClickHouse AWS        (olap_clickbench_clickhouse-aws-run-1-iteration_0_d3XK1J2u)
  - PG indexed + pgduckdb (olap_clickbench_postgresql-indexed-pgduckdb-run-1-iteration_0_9nU9BIvR)
  - PG indexed plain      (olap_clickbench_postgresql-indexed-plain-run-1-iteration_0_NhuERdJ8)

Usage:
    python utils/clickbench/plot_clickbench_latency.py
"""

import re
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2] / "results" / "clickbench" / "query"

DATASETS = {
    "ClickHouse AWS": BASE_DIR
    / "olap_clickbench_clickhouse-aws-run-1-iteration_0_d3XK1J2u"
    / "0_run.txt",
    "PG indexed + pgduckdb": BASE_DIR
    / "olap_clickbench_postgresql-indexed-pgduckdb-run-1-iteration_0_9nU9BIvR"
    / "0_run.txt",
    "PostgreSQL indexed": BASE_DIR
    / "olap_clickbench_postgresql-indexed-plain-run-1-iteration_0_NhuERdJ8"
    / "0_run.txt",
}

# Regex: [QUERY-query##], 95thPercentileLatency(us), <value>
_P95_RE = re.compile(
    r"^\[QUERY-(query\d+)\],\s*95thPercentileLatency\(us\),\s*([0-9.eE+]+)"
)

US_TO_S = 1_000_000  # microseconds → seconds


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_p95(path: Path) -> dict[str, float]:
    """Return {queryNN: latency_seconds} from a YCSB run output file."""
    results: dict[str, float] = {}
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = _P95_RE.match(line.strip())
            if m:
                query, us_str = m.group(1), m.group(2)
                results[query] = float(us_str) / US_TO_S
    return results


# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------

def plot(data: dict[str, dict[str, float]]) -> None:
    # Union of all query names, sorted numerically
    all_queries = sorted(
        {q for series in data.values() for q in series},
        key=lambda s: int(s.replace("query", "")),
    )

    labels = list(data.keys())
    n_groups = len(all_queries)
    n_bars = len(labels)
    bar_width = 0.25
    x = np.arange(n_groups)

    colors = ["#2196F3", "#FF9800", "#4CAF50"]

    fig, ax = plt.subplots(figsize=(22, 7))

    for i, (label, series) in enumerate(data.items()):
        values = [series.get(q, 0.0) for q in all_queries]
        offset = (i - n_bars / 2 + 0.5) * bar_width
        bars = ax.bar(
            x + offset,
            values,
            bar_width,
            label=label,
            color=colors[i],
            alpha=0.85,
            edgecolor="white",
            linewidth=0.4,
        )

    ax.set_xlabel("Query", fontsize=12)
    ax.set_ylabel("Cold Run Latency (seconds)", fontsize=12)
    ax.set_title(
        "ClickBench — Cold Run Latency per Query (single iteration)\n"
        "ClickHouse AWS  vs  PostgreSQL indexed + pgduckdb  vs  PostgreSQL indexed",
        fontsize=13,
        pad=14,
    )
    ax.set_xticks(x)
    ax.set_xticklabels(
        [q.replace("query", "Q") for q in all_queries],
        rotation=45,
        ha="right",
        fontsize=8,
    )
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.2f s"))
    ax.legend(fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

    fig.tight_layout()

    out_path = Path(__file__).resolve().parent / "clickbench_p95_latency.png"
    fig.savefig(out_path, dpi=150)
    print(f"Chart saved to: {out_path}")
    plt.show()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    data: dict[str, dict[str, float]] = {}
    for label, path in DATASETS.items():
        if not path.exists():
            print(f"WARNING: file not found – {path}")
            data[label] = {}
        else:
            data[label] = parse_p95(path)
            print(f"{label}: {len(data[label])} queries parsed")

    plot(data)
