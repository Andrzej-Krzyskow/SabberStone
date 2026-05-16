import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import re

RESULTS_DIR = r"D:\Pics_Movies\vids\PWr\Sem10\magisterka\RESULTS-FROM-PWR\coevolutionary_results"
OUTPUT_DIR = r"D:\Pics_Movies\vids\PWr\Sem10\magisterka\RESULTS-FROM-PWR\plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

WEIGHT_NAMES_21 = [
    "HHR","HAR","BMHR","BMAR","BMA","BMK","BSR","BMR",
    "MH","MA","MHC","MHD","MHDS","MHI","MHLS","MHS","MHT","MHW","MR","MM","MHP"
]
WEIGHT_NAMES_28 = WEIGHT_NAMES_21 + ["Br","Ręka","Zak","Prz","Smok","Jade","Pir"]

VARIANTS = {
    "modified28-":          {"label": "28-bazowy",         "num_weights": 28, "names": WEIGHT_NAMES_28},
    "modified28normalized": {"label": "28-znormalizowany", "num_weights": 28, "names": WEIGHT_NAMES_28},
    "modified21depth":      {"label": "21-głębokościowy",  "num_weights": 21, "names": WEIGHT_NAMES_21},
}

def extract_weights_from_individual_file(fpath, num_weights):
    """Odczytuje wagi najlepszego osobnika z ostatniej generacji."""
    df = pd.read_csv(fpath, header=None, skipinitialspace=True)
    # Kolumny: gen, idx_w_pop, fitness, [wagi jako lista w jednej kolumnie], BATTLES:...
    # Znajdź ostatnią generację
    last_gen = df.iloc[:, 0].max()
    last_gen_df = df[df.iloc[:, 0] == last_gen]

    # Znajdź najlepszy osobnik (max fitness dla koewolucji, min dla SHADE)
    best_row = last_gen_df.loc[last_gen_df.iloc[:, 2].astype(float).idxmax()]

    # Wyciągnij wektor wag z kolumny 3 (format "[w1, w2, ...]")
    weights_str = str(best_row.iloc[3])
    weights = [float(x) for x in re.findall(r"[\d.]+", weights_str)][:num_weights]
    return weights, float(best_row.iloc[2])

for prefix, meta in VARIANTS.items():
    pattern = os.path.join(RESULTS_DIR, f"{prefix}individuals-file-*.csv")
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"Brak plików: {prefix}")
        continue

    all_weights = []
    for fpath in files:
        try:
            w, fit = extract_weights_from_individual_file(fpath, meta["num_weights"])
            print(f"  {os.path.basename(fpath)}: fitness={fit:.1f}, wagi={[f'{x:.3f}' for x in w]}")
            all_weights.append(w)
        except Exception as e:
            print(f"  BŁĄD {fpath}: {e}")

    if not all_weights:
        continue

    arr = np.array(all_weights)
    means = arr.mean(axis=0)
    stds  = arr.std(axis=0)
    names = meta["names"][:meta["num_weights"]]
    x = np.arange(len(names))

    fig, ax = plt.subplots(figsize=(max(10, len(names) * 0.6), 5))
    bars = ax.bar(x, means, yerr=stds, capsize=4,
                  color="steelblue", alpha=0.8, ecolor="black")
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=45, ha="right", fontsize=9)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Wartość wagi")
    ax.set_title(f"Wagi najlepszych osobników — {meta['label']} (mean ± std, {len(all_weights)} run(y))")
    ax.axhline(0.5, color="gray", linestyle="--", alpha=0.5, label="w=0.5")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, f"weights_{prefix.strip('-')}.png")
    plt.savefig(out_path, dpi=150)
    print(f"Zapisano: {out_path}")
    plt.close()
