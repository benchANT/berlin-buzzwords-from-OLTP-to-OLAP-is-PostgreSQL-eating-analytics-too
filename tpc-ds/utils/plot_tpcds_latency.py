"""
Grouped bar chart comparing P95 latency per query for TPC-DS 10 GB (1-thread sequential).

Datasets:
  - ClickHouse AWS           (olap_tpc-ds_clickhouse-aws-10gb-1-thread-sequential_0_CXr4UXO4)
  - PostgreSQL + pg_duckdb   (olap_tpc-ds_postgresql-pg_duckdb-10gb-1-thread-sequential_0_9QYv4eVb)
  - PostgreSQL plain         (olap_tpc-ds_postgresql-plain-10gb-1-thread-sequential_0_4ivcQAtK)

Usage (from workspace root):
    wsl bash -c "cd /mnt/c/.../berlin-buzzwords && ~/processor_venv/bin/python utils/tpc-ds/plot_tpcds_latency.py"
"""

import re
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = (
    Path(__file__).resolve().parents[2]
    / "results"
    / "tpc-ds-original"
    / "10gb"
)

DATASETS = {
    "ClickHouse AWS": BASE_DIR
    / "olap_tpc-ds_clickhouse-aws-10gb-1-thread-sequential_0_CXr4UXO4"
    / "0_run.txt",
    "PG + pg_duckdb": BASE_DIR
    / "olap_tpc-ds_postgresql-pg_duckdb-10gb-1-thread-sequential_0_9QYv4eVb"
    / "0_run.txt",
    "PostgreSQL": BASE_DIR
    / "olap_tpc-ds_postgresql-plain-10gb-1-thread-sequential_0_4ivcQAtK"
    / "0_run.txt",
}

COLORS = ["#2196F3", "#FF9800", "#4CAF50"]

_P95_RE = re.compile(
    r"^\[QUERY-(query\d+)\],\s*95thPercentileLatency\(us\),\s*([0-9.eE+]+)"
)
US_TO_S = 1_000_000

# Mapping from internal benchmark query ID → real TPC-DS query number
QUERY_LABEL_MAP = {
    "query16": "Q03",
    "query17": "Q07",
    "query18": "Q19",
    "query19": "Q42",
    "query20": "Q52",
    "query21": "Q56",
    "query22": "Q26",
    "query23": "Q68",
    "query24": "Q73",
    "query25": "Q96",
}


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_p95(path: Path) -> dict[str, float]:
    results: dict[str, float] = {}
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = _P95_RE.match(line.strip())
            if m:
                results[m.group(1)] = float(m.group(2)) / US_TO_S
    return results


# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------

def plot(data: dict[str, dict[str, float]]) -> None:
    all_queries = sorted(
        {q for series in data.values() for q in series},
        key=lambda s: int(s.replace("query", "")),
    )

    labels = list(data.keys())
    n_bars = len(labels)
    bar_width = 0.25
    x = np.arange(len(all_queries))

    fig, ax = plt.subplots(figsize=(14, 6))

    for i, (label, series) in enumerate(data.items()):
        values = [series.get(q, 0.0) for q in all_queries]
        offset = (i - n_bars / 2 + 0.5) * bar_width
        bars = ax.bar(
            x + offset,
            values,
            bar_width,
            label=label,
            color=COLORS[i],
            alpha=0.88,
            edgecolor="white",
            linewidth=0.5,
        )
        # Value labels on top of each bar
        for bar, val in zip(bars, values):
            if val > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.04,
                    f"{val:.2f}",
                    ha="center",
                    va="bottom",
                    fontsize=6.5,
                    rotation=90,
                )

    ax.set_xlabel("TPC-DS Query", fontsize=11)
    ax.set_ylabel("P95 Latency (seconds)", fontsize=11)
    ax.set_title(
        "TPC-DS 10 GB — P95 Latency per Query (1 thread, 100 iterations)\n"
        "ClickHouse AWS  vs  PostgreSQL + pg_duckdb  vs  PostgreSQL",
        fontsize=12,
        pad=12,
    )
    ax.set_xticks(x)
    ax.set_xticklabels(
        [QUERY_LABEL_MAP.get(q, q.replace("query", "Q")) for q in all_queries],
        fontsize=10,
    )
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.1f s"))
    ax.legend(fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    # Add a bit of headroom for the value labels
    ax.set_ylim(0, ax.get_ylim()[1] * 1.25)

    fig.tight_layout()

    out_path = Path(__file__).resolve().parent / "tpcds_10gb_p95_latency.png"
    fig.savefig(out_path, dpi=150)
    print(f"Chart saved to: {out_path}")


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
