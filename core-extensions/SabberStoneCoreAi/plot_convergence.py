import pandas as pd
import matplotlib.pyplot as plt
import os
import glob

# --- KONFIGURACJA ---
RESULTS_DIR = r"D:\Pics_Movies\vids\PWr\Sem10\magisterka\RESULTS-FROM-PWR\coevolutionary_results"
OUTPUT_DIR = r"D:\Pics_Movies\vids\PWr\Sem10\magisterka\RESULTS-FROM-PWR\plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Prefixy wariantów do analizy
VARIANTS = {
    "modified21depth":      {"label": "21-głębokościowy", "num_weights": 21},
    "modified28normalized": {"label": "28-znormalizowany", "num_weights": 28},
    "modified28-":          {"label": "28-bazowy",         "num_weights": 28},
    "modified63smooth":     {"label": "63-płynny",         "num_weights": 63},
    "modified63-":          {"label": "63-fazowy",         "num_weights": 63},
}

# Kolumny statistics-file:
# generacja, rozmiar_pop, worst, best, median, avg, std, czas
STATS_COLS = ["gen", "pop_size", "worst", "best", "median", "avg", "std", "elapsed"]

fig, axes = plt.subplots(len(VARIANTS), 1, figsize=(10, 4 * len(VARIANTS)), sharex=False)
if len(VARIANTS) == 1:
    axes = [axes]

for ax, (prefix, meta) in zip(axes, VARIANTS.items()):
    pattern = os.path.join(RESULTS_DIR, f"{prefix}statistics-file-*.csv")
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"Brak plików dla: {prefix}")
        continue

    print(f"{meta['label']}: znaleziono {len(files)} run(ów)")

    for i, fpath in enumerate(files):
        df = pd.read_csv(fpath, header=None, names=STATS_COLS,
                         skipinitialspace=True)
        df = df.apply(pd.to_numeric, errors='coerce').dropna()

        ax.plot(df["gen"], df["best"],  label=f"Run {i+1} — best",  linewidth=1.5)
        ax.fill_between(df["gen"],
                        df["best"] - df["std"],
                        df["best"] + df["std"],
                        alpha=0.15)

    ax.set_title(f"Konwergencja — {meta['label']}")
    ax.set_xlabel("Generacja")
    ax.set_ylabel("Fitness (wygrane)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
out_path = os.path.join(OUTPUT_DIR, "convergence_all_variants.png")
plt.savefig(out_path, dpi=150)
print(f"Zapisano: {out_path}")
plt.close()
