import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import os
import glob
import re

RESULTS_DIR = r"D:\Pics_Movies\vids\PWr\Sem10\magisterka\SabberStone\core-extensions\SabberStoneCoreAi\analysis\results"
OUTPUT_DIR  = r"D:\Pics_Movies\vids\PWr\Sem10\magisterka\SabberStone\core-extensions\SabberStoneCoreAi\analysis\plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -----------------------------------------------------------------------
# BLOK A — koewolucja
# -----------------------------------------------------------------------
VARIANTS = {
    "modified28-":           {"label": "28-bazowy",        "num_weights": 28, "minimize": False},
    "modified28normalized-": {"label": "28-znormalizowany","num_weights": 28, "minimize": False},
    "modified21depth-":      {"label": "21-głębokościowy", "num_weights": 21, "minimize": False},
    "modified63smooth-":     {"label": "63-płynny",        "num_weights": 63, "minimize": False},
    "modified63-":           {"label": "63-fazowy",        "num_weights": 63, "minimize": False},
}

# -----------------------------------------------------------------------
# BLOK B — SHADE
# -----------------------------------------------------------------------
# VARIANTS = {
#     "shade-like-15-":      {"label": "SHADE-21", "num_weights": 21, "minimize": True},
# }

# -----------------------------------------------------------------------

def parse_individuals_file(fpath, num_weights):
    """
    Parsuje plik individuals i zwraca listę krotek:
    (gen, idx, fitness, identity)
    gdzie identity = tuple pierwszych num_weights wag (unikalny ID osobnika).
    """
    rows = []
    with open(fpath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            header = re.match(r'^\s*(\d+)\s*,\s*(\d+)\s*,\s*([-\d.]+)\s*,', line)
            bracket = re.search(r'\[([^\]]+)\]', line)
            if not header or not bracket:
                continue
            gen     = int(header.group(1))
            idx     = int(header.group(2))
            fitness = float(header.group(3))
            weights = [float(x.strip()) for x in bracket.group(1).split(",") if x.strip()][:num_weights]
            if len(weights) < num_weights:
                continue
            # Zaokrąglamy do 6 miejsc żeby uniknąć błędów float przy porównaniu
            identity = tuple(round(w, 6) for w in weights)
            rows.append((gen, idx, fitness, identity))
    return rows


def compute_age_stats(rows):
    """
    Dla każdego osobnika (identity) zlicza:
    - FIRST: pierwsza generacja w której się pojawił
    - LAST:  ostatnia generacja w której się pojawił
    - AGE = LAST - FIRST + 1
    Zwraca DataFrame z kolumnami: IDENTITY, FIRST, LAST, AGE, FITNESS
    """
    seen = {}  # identity -> {first, last, fitness}
    for gen, idx, fitness, identity in rows:
        if identity not in seen:
            seen[identity] = {"first": gen, "last": gen, "fitness": fitness}
        else:
            seen[identity]["last"] = max(seen[identity]["last"], gen)

    records = []
    for identity, d in seen.items():
        records.append({
            "FIRST":   d["first"],
            "LAST":    d["last"],
            "AGE":     d["last"] - d["first"] + 1,
            "FITNESS": d["fitness"],
        })
    return pd.DataFrame(records)


def compute_new_per_gen(rows):
    """
    Dla każdej generacji zlicza ile nowych osobników (CURRENT_AGE == 0,
    tzn. pojawia się po raz pierwszy) weszło do populacji.
    """
    first_seen = {}
    gen_new = {}
    for gen, idx, fitness, identity in rows:
        if identity not in first_seen:
            first_seen[identity] = gen
            gen_new[gen] = gen_new.get(gen, 0) + 1
    return gen_new


# -----------------------------------------------------------------------
# Główna pętla — jeden wykres per wariant
# -----------------------------------------------------------------------
for prefix, meta in VARIANTS.items():
    pattern = os.path.join(RESULTS_DIR, f"{prefix}individuals-file-*.csv")
    files   = sorted(glob.glob(pattern))

    if not files:
        print(f"Brak plików: {prefix}")
        continue

    if len(files) > 1:
        print(f"UWAGA: {len(files)} plików dla '{prefix}' — używam pierwszego")

    fpath = files[0]
    label = meta["label"]
    print(f"Przetwarzam: {label} ({os.path.basename(fpath)})")

    rows = parse_individuals_file(fpath, meta["num_weights"])
    if not rows:
        print(f"  Brak danych w pliku.")
        continue

    df_age   = compute_age_stats(rows)
    gen_new  = compute_new_per_gen(rows)
    all_gens = sorted(set(r[0] for r in rows))
    n_gens   = len(all_gens)

    print(f"  Łącznie unikalnych osobników: {len(df_age)}")
    print(f"  Generacje: {all_gens[0]}–{all_gens[-1]}")
    print(f"  Śr. wiek osobnika: {df_age['AGE'].mean():.2f} gen")

    # -----------------------------------------------------------------------
    # Wykres — 3 subploty
    # -----------------------------------------------------------------------
    fig, axes = plt.subplots(3, 1, figsize=(11, 13))
    fig.suptitle(f"Analiza pokoleń — {label}", fontsize=13, fontweight="bold")

    # --- Subplot 1: Liczba nowych osobników per generacja ---
    ax1 = axes[0]
    xs  = sorted(gen_new.keys())
    ys  = [gen_new[g] for g in xs]
    ax1.bar(xs, ys, color="#4878CF", alpha=0.8, edgecolor="white")
    ax1.set_title("Nowe osobniki w każdej generacji")
    ax1.set_xlabel("Generacja")
    ax1.set_ylabel("Liczba nowych osobników")
    ax1.grid(axis="y", alpha=0.3, linestyle=":")
    # Linia średnia
    mean_new = np.mean(ys)
    ax1.axhline(mean_new, color="red", linestyle="--", alpha=0.7,
                label=f"Średnia: {mean_new:.1f}")
    ax1.legend(fontsize=8)

    # --- Subplot 2: Rozkład wieku osobników (histogram) ---
    ax2 = axes[1]
    ages = df_age["AGE"].values
    max_age = int(ages.max())
    bins = range(1, max_age + 2)
    ax2.hist(ages, bins=bins, color="#6ACC65", alpha=0.8, edgecolor="white", align="left")
    ax2.set_title("Rozkład wieku osobników (ile generacji przeżył)")
    ax2.set_xlabel("Wiek (liczba generacji)")
    ax2.set_ylabel("Liczba osobników")
    ax2.axvline(ages.mean(), color="red", linestyle="--", alpha=0.7,
                label=f"Średnia: {ages.mean():.2f}")
    ax2.axvline(np.median(ages), color="orange", linestyle="--", alpha=0.7,
                label=f"Mediana: {np.median(ages):.1f}")
    ax2.legend(fontsize=8)
    ax2.grid(axis="y", alpha=0.3, linestyle=":")

    # --- Subplot 3: Boxplot wieku per generacja (co ~5 gen) ---
    ax3 = axes[2]

    # Dla każdego osobnika zapamiętaj generację pierwszego pojawienia się
    first_seen_map = {}
    for gen, idx, fitness, identity in sorted(rows, key=lambda r: r[0]):
        if identity not in first_seen_map:
            first_seen_map[identity] = gen

    # Zbierz aktualny wiek każdego osobnika w jego generacji
    gen_current_ages = {g: [] for g in all_gens}
    for gen, idx, fitness, identity in rows:
        current_age = gen - first_seen_map[identity]
        gen_current_ages[gen].append(current_age)

    step       = max(1, n_gens // 20)
    plot_gens  = [g for g in all_gens if g % step == 0]
    plot_data  = [gen_current_ages[g] for g in plot_gens if gen_current_ages[g]]
    plot_gens  = [g for g in plot_gens if gen_current_ages[g]]

    ax3.boxplot(plot_data, positions=plot_gens,
                widths=step * 0.6, patch_artist=True,
                boxprops=dict(facecolor="#D65F5F", alpha=0.7),
                medianprops=dict(color="black", linewidth=1.5),
                flierprops=dict(marker=".", markersize=3, alpha=0.4))
    ax3.set_title("Wiek osobników w każdej generacji (aktywni osobnicy)")
    ax3.set_xlabel("Generacja")
    ax3.set_ylabel("Aktualny wiek (gen - gen_urodzenia)")
    ax3.grid(axis="y", alpha=0.3, linestyle=":")

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, f"generations_{prefix.strip('-')}.png")
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"  Zapisano: {out_path}")
