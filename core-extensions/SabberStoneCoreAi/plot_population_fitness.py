import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import re

RESULTS_DIR = r"D:\Pics_Movies\vids\PWr\Sem10\magisterka\SabberStone\core-extensions\SabberStoneCoreAi\analysis\results"
OUTPUT_DIR  = r"D:\Pics_Movies\vids\PWr\Sem10\magisterka\SabberStone\core-extensions\SabberStoneCoreAi\analysis\plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -----------------------------------------------------------------------
# BLOK A — koewolucja (minimize=False)
# -----------------------------------------------------------------------
VARIANTS = {
    "modified21depth-":      {"label": "21-głębokościowy", "minimize": False},
    "modified28normalized-": {"label": "28-znormalizowany","minimize": False},
    "modified28-":           {"label": "28-bazowy",        "minimize": False},
    "modified63smooth-":     {"label": "63-płynny",        "minimize": False},
    "modified63-":           {"label": "63-fazowy",        "minimize": False},
}

# -----------------------------------------------------------------------
# BLOK B — SHADE (minimize=True) — zakomentuj BLOK A i odkomentuj to
# -----------------------------------------------------------------------
# VARIANTS = {
#     "shade-like-15-":                        {"label": "SHADE-like-21",       "minimize": True},
#     "shade-like-15-modified28-":             {"label": "SHADE-like-28",       "minimize": True},
#     "shade-like-15-modified28-normalized-":  {"label": "SHADE-like-28-norm",  "minimize": True},
#     "shade-like-15-modified63-smooth-":      {"label": "SHADE-like-63-płynny","minimize": True},
#     "shade-like-15-modified63-":             {"label": "SHADE-like-63-bazowy","minimize": True},
# }

# -----------------------------------------------------------------------

def parse_fitness_per_gen(fpath, minimize):
    gen_fitness = {}
    with open(fpath, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(r'^\s*(\d+)\s*,\s*\d+\s*,\s*([-\d.]+)\s*,', line.strip())
            if m:
                gen = int(m.group(1))
                fit = abs(float(m.group(2)))  # abs: SHADE przechowuje ujemne
                gen_fitness.setdefault(gen, []).append(fit)
    return gen_fitness


for prefix, meta in VARIANTS.items():
    pattern = os.path.join(RESULTS_DIR, f"{prefix}individuals-file-*.csv")
    files   = sorted(glob.glob(pattern))

    if not files:
        print(f"Brak plików: {prefix}")
        continue
    if len(files) > 1:
        print(f"UWAGA: {len(files)} plików dla '{prefix}' — używam pierwszego")

    gen_fitness = parse_fitness_per_gen(files[0], meta["minimize"])
    if not gen_fitness:
        print(f"Brak danych: {prefix}")
        continue

    gens      = sorted(gen_fitness.keys())
    step      = max(1, len(gens) // 20)
    plot_gens = [g for g in gens if g % step == 0]
    plot_data = [gen_fitness[g] for g in plot_gens]

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.boxplot(plot_data, positions=plot_gens, widths=step * 0.6,
               patch_artist=True,
               boxprops=dict(facecolor="#4878CF", alpha=0.6),
               medianprops=dict(color="black", linewidth=2),
               flierprops=dict(marker=".", markersize=3, alpha=0.3))
    ax.set_title(f"Rozkład fitness populacji per generacja — {meta['label']}")
    ax.set_xlabel("Generacja")
    ax.set_ylabel("Fitness (liczba wygranych)")
    ax.grid(axis="y", alpha=0.25, linestyle=":")
    plt.tight_layout()

    out_path = os.path.join(OUTPUT_DIR, f"pop_fitness_{prefix.strip('-')}.png")
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Zapisano: {out_path}")
