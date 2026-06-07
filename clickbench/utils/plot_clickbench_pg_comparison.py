"""
Grouped bar chart: PG indexed + pgduckdb  vs  PG indexed plain — P95 latency per query.

Queries are split into three subplots by latency tier so each chart is readable:
  Tier 1 – Fast   : max P95 across both datasets  <  15 s
  Tier 2 – Medium : max P95 between 15 s and 150 s
  Tier 3 – Heavy  : max P95 >= 150 s

Usage:
    wsl bash -c "cd /mnt/c/... && ~/processor_venv/bin/python utils/clickbench/plot_clickbench_pg_comparison.py"
"""

import re
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2] / "results" / "clickbench" / "query"

DATASETS = {
    "PG indexed + pgduckdb": BASE_DIR
    / "olap_clickbench_postgresql-indexed-pgduckdb-run-1-iteration_0_9nU9BIvR"
    / "0_run.txt",
    "PostgreSQL indexed": BASE_DIR
    / "olap_clickbench_postgresql-indexed-plain-run-1-iteration_0_NhuERdJ8"
    / "0_run.txt",
}

COLORS = ["#FF9800", "#4CAF50"]

_P95_RE = re.compile(
    r"^\[QUERY-(query\d+)\],\s*95thPercentileLatency\(us\),\s*([0-9.eE+]+)"
)
US_TO_S = 1_000_000

TIER_FAST_MAX_S   = 15
TIER_MEDIUM_MAX_S = 150


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
# Grouping
# ---------------------------------------------------------------------------

def group_queries(data: dict[str, dict[str, float]]) -> tuple[list, list, list]:
    all_queries = sorted(
        {q for series in data.values() for q in series},
        key=lambda s: int(s.replace("query", "")),
    )
    fast, medium, heavy = [], [], []
    for q in all_queries:
        max_val = max(series.get(q, 0.0) for series in data.values())
        if max_val < TIER_FAST_MAX_S:
            fast.append(q)
        elif max_val < TIER_MEDIUM_MAX_S:
            medium.append(q)
        else:
            heavy.append(q)
    return fast, medium, heavy


# ---------------------------------------------------------------------------
# Plot helper
# ---------------------------------------------------------------------------

def draw_subplot(
    ax: plt.Axes,
    queries: list[str],
    data: dict[str, dict[str, float]],
    title: str,
) -> None:
    labels = list(data.keys())
    n_bars = len(labels)
    bar_width = 0.35
    x = np.arange(len(queries))

    for i, (label, series) in enumerate(data.items()):
        values = [series.get(q, 0.0) for q in queries]
        offset = (i - n_bars / 2 + 0.5) * bar_width
        ax.bar(
            x + offset,
            values,
            bar_width,
            label=label,
            color=COLORS[i],
            alpha=0.88,
            edgecolor="white",
            linewidth=0.4,
        )

    ax.set_title(title, fontsize=11, pad=8)
    ax.set_ylabel("Cold Run Latency (seconds)", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(
        [q.replace("query", "Q") for q in queries],
        rotation=45,
        ha="right",
        fontsize=8,
    )
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.1f s"))
    ax.legend(fontsize=8)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    data: dict[str, dict[str, float]] = {}
    for label, path in DATASETS.items():
        if not path.exists():
            print(f"WARNING: file not found – {path}")
            data[label] = {}
        else:
            data[label] = parse_p95(path)
            print(f"{label}: {len(data[label])} queries parsed")

    fast, medium, heavy = group_queries(data)
    print(f"Tier 1 Fast   ({len(fast)} queries):   {[q.replace('query','Q') for q in fast]}")
    print(f"Tier 2 Medium ({len(medium)} queries): {[q.replace('query','Q') for q in medium]}")
    print(f"Tier 3 Heavy  ({len(heavy)} queries):  {[q.replace('query','Q') for q in heavy]}")

    fig, axes = plt.subplots(
        3, 1,
        figsize=(18, 16),
        gridspec_kw={"hspace": 0.55},
    )

    draw_subplot(
        axes[0], fast, data,
        f"Tier 1 – Fast queries  (cold run < {TIER_FAST_MAX_S} s)",
    )
    draw_subplot(
        axes[1], medium, data,
        f"Tier 2 – Medium queries  ({TIER_FAST_MAX_S} s ≤ cold run < {TIER_MEDIUM_MAX_S} s)",
    )
    draw_subplot(
        axes[2], heavy, data,
        f"Tier 3 – Heavy queries  (cold run ≥ {TIER_MEDIUM_MAX_S} s)",
    )

    fig.suptitle(
        "ClickBench — Cold Run Latency per Query (single iteration, indexed)\n"
        "PostgreSQL + pgduckdb  vs  PostgreSQL indexed",
        fontsize=13,
        y=0.98,
    )

    out_path = Path(__file__).resolve().parent / "clickbench_pg_p95_comparison.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"\nChart saved to: {out_path}")


if __name__ == "__main__":
    main()
