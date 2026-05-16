import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import re

RESULTS_DIR = r"D:\Pics_Movies\vids\PWr\Sem10\magisterka\RESULTS-FROM-PWR\coevolutionary_results"
OUTPUT_DIR = r"D:\Pics_Movies\vids\PWr\Sem10\magisterka\RESULTS-FROM-PWR\plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 9 kombinacji talii (kolejność z kodu: d1 x d2)
DECKS = ["RenoKazakusMage", "MidrangeJadeShaman", "AggroPirateWarrior"]
BATTLE_COLS = [f"{d1[:4]}vs{d2[:4]}" for d1 in DECKS for d2 in DECKS]

def extract_battles(fpath):
    """Wyciąga sumaryczne wygrane per kombinacja talii z ostatniej generacji."""
    totals = np.zeros(9)
    with open(fpath, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(", ")
            if len(parts) < 4:
                continue
            # Szukamy wiersza z BATTLES:
            battles_part = [p for p in parts if "BATTLES:" in p]
            if not battles_part:
                continue
            battle_str = battles_part[0].replace("BATTLES:", "").strip().rstrip("-")
            vals = [int(x) for x in battle_str.split("-") if x.strip().isdigit()]
            if len(vals) == 9:
                totals += np.array(vals)
    return totals

VARIANTS = {
    "modified28-":          "28-bazowy",
    "modified28normalized": "28-znormalizowany",
    "modified21depth":      "21-głębokościowy",
    "modified63-":          "63-fazowy",
    "modified63smooth":     "63-płynny",
}

summary = {}
for prefix, label in VARIANTS.items():
    pattern = os.path.join(RESULTS_DIR, f"{prefix}individuals-file-*.csv")
    files = sorted(glob.glob(pattern))
    if not files:
        continue
    run_totals = []
    for fpath in files:
        totals = extract_battles(fpath)
        run_totals.append(totals)
    if run_totals:
        summary[label] = np.mean(run_totals, axis=0)

if summary:
    df_battles = pd.DataFrame(summary, index=BATTLE_COLS).T
    fig, ax = plt.subplots(figsize=(12, 5))
    x = np.arange(len(BATTLE_COLS))
    width = 0.8 / len(summary)
    for i, (label, vals) in enumerate(summary.items()):
        ax.bar(x + i * width, vals, width, label=label, alpha=0.85)
    ax.set_xticks(x + width * len(summary) / 2)
    ax.set_xticklabels(BATTLE_COLS, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Łączne wygrane (avg per run)")
    ax.set_title("Wygrane per kombinacja talii — porównanie wariantów")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "battles_per_deck.png"), dpi=150)
    plt.close()
    print("Zapisano battles_per_deck.png")
