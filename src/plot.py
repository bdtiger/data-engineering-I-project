import matplotlib.pyplot as plt
import csv

def plot_horizontal_scaling(results):
    # ── Strong Horizontal Scaling ─────────────────────────────────────────────────
    workers = [1, 2, 3]
    h_times = [results["H-1"], results["H-2"], results["H-3"]]

    T1 = h_times[0]
    h_speedup = [T1 / t for t in h_times]
    ideal_speedup = [1, 2, 3]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    fig.suptitle("Horizontal Scaling (Strong)")

    bars_h = axes[0].bar(workers, h_times, color='steelblue', label='Actual')
    axes[0].bar_label(bars_h, padding=3)
    axes[0].set_title("Runtime vs Number of Workers")
    axes[0].set_xlabel("Number of Workers")
    axes[0].set_ylabel("Runtime (seconds)")
    axes[0].set_xticks(workers)
    axes[0].grid(axis='y')

    axes[1].plot(workers, h_speedup, 'o-', color='steelblue', label='Actual speedup')
    axes[1].plot(workers, ideal_speedup, 's--', color='gray', label='Ideal speedup')
    axes[1].set_title("Speedup vs Ideal")
    axes[1].set_xlabel("Number of Workers")
    axes[1].set_ylabel("Speedup (T1 / Tn)")
    axes[1].set_xticks(workers)
    axes[1].legend()
    axes[1].grid(True)

    plt.tight_layout()
    plt.savefig("project-report/figures/horizontal_scaling.png", dpi=150)
    plt.show()

def plot_vertical_scaling(results):
    # ── Vertical Scaling ──────────────────────────────────────────────────────────
    cores = [1, 2]
    v_times = [results["V-1"], results["V-2"]]

    T1_v = v_times[0]
    v_speedup = [T1_v / t for t in v_times]
    ideal_v = [1, 2]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    fig.suptitle("Vertical Scaling")

    bars_v = axes[0].bar(cores, v_times, color='darkorange', width=0.4)
    axes[0].bar_label(bars_v, padding=3)
    axes[0].set_title("Runtime vs Cores per Executor")
    axes[0].set_xlabel("Cores per Executor")
    axes[0].set_ylabel("Runtime (seconds)")
    axes[0].set_xticks(cores)
    axes[0].grid(axis='y')

    axes[1].plot(cores, v_speedup, 'o-', color='darkorange', label='Actual speedup')
    axes[1].plot(cores, ideal_v, 's--', color='gray', label='Ideal speedup')
    axes[1].set_title("Speedup vs Ideal")
    axes[1].set_xlabel("Cores per Executor")
    axes[1].set_ylabel("Speedup (T1 / Tn)")
    axes[1].set_xticks(cores)
    axes[1].legend()
    axes[1].grid(True)

    plt.tight_layout()
    plt.savefig("project-report/figures/vertical_scaling.png", dpi=150)
    plt.show()

if __name__ == "__main__":
    # ── Load timings.csv ─────────────────────────────────────────────────────────
    results_data = {}
    with open("results/timings.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            results_data[row["experiment"]] = int(row["runtime_seconds"])

    plot_horizontal_scaling(results_data)
    plot_vertical_scaling(results_data)