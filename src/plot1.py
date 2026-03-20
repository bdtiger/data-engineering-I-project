import matplotlib.pyplot as plt
import csv
import os

# ── Configuration ────────────────────────────────────────────────────────────
CACHED_CSV = os.path.join(os.path.dirname(__file__), "..", "results", "with_os_caching", "timings.csv")
COLD_CSV = os.path.join(os.path.dirname(__file__), "..", "results", "timings.csv")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "project-report", "figures")


def load_csv(path):
    """Load timings CSV into a dict keyed by experiment label."""
    data = {}
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            data[row["experiment"]] = {
                "workers": int(row["workers"]),
                "cores": int(row["cores_per_executor"]),
                "data_gb": int(row["data_gb"]),
                "etl": int(row["etl_runtime_seconds"]),
                "analysis": int(row["analysis_runtime_seconds"]),
                "total": int(row["total_runtime_seconds"]),
            }
    return data


# ── Plot 1: Horizontal Strong Scaling ────────────────────────────────────────
def plot_horizontal_scaling(results):
    workers = [1, 2, 3]
    totals = [results["H-1"]["total"], results["H-2"]["total"], results["H-3"]["total"]]
    etls = [results["H-1"]["etl"], results["H-2"]["etl"], results["H-3"]["etl"]]
    analysis = [results["H-1"]["analysis"], results["H-2"]["analysis"], results["H-3"]["analysis"]]
    ideal = [totals[0], totals[0] / 2, totals[0] / 3]

    T1 = totals[0]
    speedups = [T1 / t for t in totals]
    ideal_speedup = [1, 2, 3]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    fig.suptitle("Horizontal Strong Scaling (5 GB, 2 cores/executor)", fontweight='bold')

    # Left: Runtime breakdown (bars + lines)
    width = 0.2
    axes[0].bar([w - width for w in workers], totals, width, color='steelblue', alpha=0.35)
    axes[0].bar(workers, analysis, width, color='darkorange', alpha=0.35)
    axes[0].bar([w + width for w in workers], etls, width, color='indianred', alpha=0.35)
    axes[0].plot(workers, totals, 'o-', color='steelblue', label='Total', linewidth=2)
    axes[0].plot(workers, analysis, 's-', color='darkorange', label='Analysis', linewidth=2)
    axes[0].plot(workers, etls, '^-', color='indianred', label='ETL', linewidth=2)
    axes[0].plot(workers, ideal, 's--', color='gray', label='Ideal Total', linewidth=1.5)
    axes[0].set_title("Runtime vs Number of Workers")
    axes[0].set_xlabel("Number of Workers")
    axes[0].set_ylabel("Runtime (seconds)")
    axes[0].set_xticks(workers)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Right: Speedup
    axes[1].plot(workers, speedups, 'o-', color='steelblue', label='Actual speedup', linewidth=2)
    axes[1].plot(workers, ideal_speedup, 's--', color='gray', label='Ideal speedup', linewidth=1.5)
    axes[1].set_title("Speedup vs Ideal")
    axes[1].set_xlabel("Number of Workers")
    axes[1].set_ylabel("Speedup (T₁ / Tₙ)")
    axes[1].set_xticks(workers)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "horizontal_scaling.png"), dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ horizontal_scaling.png")


# ── Plot 2: Weak Scaling ─────────────────────────────────────────────────────
def plot_weak_scaling(results):
    workers = [1, 2]
    totals = [results["W-1"]["total"], results["W-2"]["total"]]
    etls = [results["W-1"]["etl"], results["W-2"]["etl"]]
    analysis = [results["W-1"]["analysis"], results["W-2"]["analysis"]]
    ideal_runtime = [totals[0], totals[0]]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    fig.suptitle("Weak Scaling (Workers ∝ Data)", fontweight='bold')

    # Left: Runtime (bars + lines)
    width = 0.15
    axes[0].bar([w - width for w in workers], totals, width, color='seagreen', alpha=0.35)
    axes[0].bar(workers, analysis, width, color='darkorange', alpha=0.35)
    axes[0].bar([w + width for w in workers], etls, width, color='indianred', alpha=0.35)
    axes[0].plot(workers, totals, 'o-', color='seagreen', label='Total', linewidth=2)
    axes[0].plot(workers, analysis, 's-', color='darkorange', label='Analysis', linewidth=2)
    axes[0].plot(workers, etls, '^-', color='indianred', label='ETL', linewidth=2)
    axes[0].plot(workers, ideal_runtime, 's--', color='gray', label='Ideal (constant)', linewidth=1.5)
    axes[0].set_title("Runtime vs Workers/Data")
    axes[0].set_xlabel("Workers / Data Size")
    axes[0].set_ylabel("Runtime (seconds)")
    axes[0].set_xticks(workers)
    axes[0].set_xticklabels(["1 Worker\n(5 GB)", "2 Workers\n(10 GB)"])
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Right: Runtime bar comparison
    x = [0, 1]
    width = 0.25
    bars1 = axes[1].bar([i - width for i in x], totals, width, color='seagreen', label='Total')
    bars2 = axes[1].bar(x, analysis, width, color='darkorange', label='Analysis')
    bars3 = axes[1].bar([i + width for i in x], etls, width, color='indianred', label='ETL')
    axes[1].bar_label(bars1, padding=3)
    axes[1].bar_label(bars2, padding=3)
    axes[1].bar_label(bars3, padding=3)
    axes[1].set_title("Runtime Breakdown")
    axes[1].set_xlabel("Configuration")
    axes[1].set_ylabel("Runtime (seconds)")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(["W-1\n(1w / 5GB)", "W-2\n(2w / 10GB)"])
    axes[1].legend()
    axes[1].grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "weak_scaling.png"), dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ weak_scaling.png")


# ── Plot 3: Vertical Scaling (5 GB + 10 GB combined) ─────────────────────────
def plot_vertical_scaling(results):
    cores = [1, 2]

    # 5 GB
    v5_totals = [results["V-1"]["total"], results["V-2"]["total"]]
    v5_speedup = [1, v5_totals[0] / v5_totals[1]]

    # 10 GB
    v10_totals = [results["V-3"]["total"], results["V-4"]["total"]]
    v10_speedup = [1, v10_totals[0] / v10_totals[1]]

    ideal_speedup = [1, 2]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    fig.suptitle("Vertical Scaling (3 Workers Fixed)", fontweight='bold')

    # Left: Runtime (bars + lines)
    width = 0.15
    axes[0].bar([c - width / 2 for c in cores], v5_totals, width, color='darkorange', alpha=0.35)
    axes[0].bar([c + width / 2 for c in cores], v10_totals, width, color='purple', alpha=0.35)
    axes[0].plot(cores, v5_totals, 'o-', color='darkorange', label='5 GB', linewidth=2)
    axes[0].plot(cores, v10_totals, 's-', color='purple', label='10 GB', linewidth=2)
    axes[0].plot(cores, [v5_totals[0], v5_totals[0] / 2], 'o--', color='darkorange', alpha=0.5, label='5 GB Ideal')
    axes[0].plot(cores, [v10_totals[0], v10_totals[0] / 2], 's--', color='purple', alpha=0.5, label='10 GB Ideal')
    axes[0].set_title("Runtime vs Cores per Executor")
    axes[0].set_xlabel("Cores per Executor")
    axes[0].set_ylabel("Runtime (seconds)")
    axes[0].set_xticks(cores)
    axes[0].set_xticklabels(["1 core\n(3 total)", "2 cores\n(6 total)"])
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Right: Speedup
    axes[1].plot(cores, v5_speedup, 'o-', color='darkorange', label='5 GB Actual', linewidth=2)
    axes[1].plot(cores, v10_speedup, 's-', color='purple', label='10 GB Actual', linewidth=2)
    axes[1].plot(cores, ideal_speedup, 's--', color='gray', label='Ideal speedup', linewidth=1.5)
    axes[1].set_title("Speedup vs Ideal")
    axes[1].set_xlabel("Cores per Executor")
    axes[1].set_ylabel("Speedup (T₁ / T₂)")
    axes[1].set_xticks(cores)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "vertical_scaling.png"), dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ vertical_scaling.png")


# ── Plot 4: Speedup & Efficiency Summary ─────────────────────────────────────
def plot_speedup_efficiency(results):
    experiments = ["H (1→3w)", "V-5GB (1→2c)", "V-10GB (1→2c)", "W (1w→2w)"]

    T_h1, T_h3 = results["H-1"]["total"], results["H-3"]["total"]
    T_v1, T_v2 = results["V-1"]["total"], results["V-2"]["total"]
    T_v3, T_v4 = results["V-3"]["total"], results["V-4"]["total"]
    T_w1, T_w2 = results["W-1"]["total"], results["W-2"]["total"]

    speedups = [T_h1 / T_h3, T_v1 / T_v2, T_v3 / T_v4, T_w1 / T_w2]
    p_factors = [3, 2, 2, 2]
    efficiencies = [s / p for s, p in zip(speedups, p_factors)]

    x = range(len(experiments))
    width = 0.3

    fig, ax = plt.subplots(figsize=(9, 5))

    bars1 = ax.bar([i - width / 2 for i in x], speedups, width, color='steelblue', label='Speedup')
    bars2 = ax.bar([i + width / 2 for i in x], efficiencies, width, color='darkorange', label='Efficiency')
    ax.bar_label(bars1, fmt='%.2f', padding=3, fontsize=9)
    ax.bar_label(bars2, fmt='%.2f', padding=3, fontsize=9)

    ax.set_title("Speedup and Efficiency Comparison", fontweight='bold')
    ax.set_xlabel("Scaling Experiment")
    ax.set_ylabel("Value")
    ax.set_xticks(x)
    ax.set_xticklabels(experiments)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "speedup_efficiency.png"), dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ speedup_efficiency.png")


# ── Plot 5: Cold Cache vs Hot Cache Comparison ───────────────────────────────
def plot_cold_vs_hot(cached, cold):
    phases = ["ETL", "Analysis", "Total"]
    hot_vals = [cached["H-3"]["etl"], cached["H-3"]["analysis"], cached["H-3"]["total"]]
    cold_vals = [cold["H-3"]["etl"], cold["H-3"]["analysis"], cold["H-3"]["total"]]

    x = range(len(phases))
    width = 0.3

    fig, ax = plt.subplots(figsize=(8, 5))

    bars1 = ax.bar([i - width / 2 for i in x], cold_vals, width, color='#e74c3c', label='Cold Cache')
    bars2 = ax.bar([i + width / 2 for i in x], hot_vals, width, color='#2ecc71', label='Hot Cache')
    ax.bar_label(bars1, padding=3)
    ax.bar_label(bars2, padding=3)

    ax.set_title("Cold Cache vs Hot Cache (H-3: 3 Workers, 2 Cores, 5 GB)", fontweight='bold')
    ax.set_xlabel("Pipeline Phase")
    ax.set_ylabel("Runtime (seconds)")
    ax.set_xticks(x)
    ax.set_xticklabels(phases)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "cold_vs_hot_cache.png"), dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ cold_vs_hot_cache.png")


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    cached = load_csv(CACHED_CSV)
    cold = load_csv(COLD_CSV)

    print(f"Loaded {len(cached)} experiments from with_os_caching/timings.csv")
    print(f"Loaded {len(cold)} experiments from timings.csv (cold cache)")
    print(f"Saving plots to {OUTPUT_DIR}\n")

    plot_horizontal_scaling(cached)
    plot_weak_scaling(cached)
    plot_vertical_scaling(cached)
    plot_speedup_efficiency(cached)
    plot_cold_vs_hot(cached, cold)

    print("\nAll plots generated successfully!")
