import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os
import glob
import re
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from sklearn.metrics import silhouette_score

RESULTS_DIR = r"D:\Pics_Movies\vids\PWr\Sem10\magisterka\SabberStone\core-extensions\SabberStoneCoreAi\analysis\results"
OUTPUT_DIR  = r"D:\Pics_Movies\vids\PWr\Sem10\magisterka\SabberStone\core-extensions\SabberStoneCoreAi\analysis\plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

WEIGHT_NAMES_21 = [
    "HHR","HAR","BMHR","BMAR","BMA","BMK","BSR","BMR",
    "MH","MA","MHC","MHD","MHDS","MHI","MHLS","MHS","MHT","MHW","MR","MM","MHP"
]
WEIGHT_NAMES_28 = WEIGHT_NAMES_21 + ["Br","Ręka","Zak","Prz","Smok","Jade","Pir"]
WEIGHT_NAMES_63 = (
    [f"{n}_1" for n in WEIGHT_NAMES_21] +
    [f"{n}_2" for n in WEIGHT_NAMES_21] +
    [f"{n}_3" for n in WEIGHT_NAMES_21]
)

# -----------------------------------------------------------------------
# BLOK A — koewolucja (minimize=False)
# -----------------------------------------------------------------------
VARIANTS = {
    "modified21depth-":      {"label": "21-głębokościowy", "num_weights": 21, "names": WEIGHT_NAMES_21, "minimize": False, "smooth": False},
    "modified28normalized-": {"label": "28-znormalizowany","num_weights": 28, "names": WEIGHT_NAMES_28, "minimize": False, "smooth": False},
    "modified28-":           {"label": "28-bazowy",        "num_weights": 28, "names": WEIGHT_NAMES_28, "minimize": False, "smooth": False},
    "modified63smooth-":     {"label": "63-płynny",        "num_weights": 63, "names": WEIGHT_NAMES_63, "minimize": False, "smooth": True},
    "modified63-":           {"label": "63-fazowy",        "num_weights": 63, "names": WEIGHT_NAMES_63, "minimize": False, "smooth": False},
}

# -----------------------------------------------------------------------
# BLOK B — SHADE (minimize=True) — zakomentuj BLOK A i odkomentuj to
# -----------------------------------------------------------------------
# VARIANTS = {
#     "shade-like-15-":                        {"label": "SHADE-like-21",        "num_weights": 21, "names": WEIGHT_NAMES_21, "minimize": True, "smooth": False},
#     "shade-like-15-modified28-":             {"label": "SHADE-like-28",        "num_weights": 28, "names": WEIGHT_NAMES_28, "minimize": True, "smooth": False},
#     "shade-like-15-modified28-normalized-":  {"label": "SHADE-like-28-norm",   "num_weights": 28, "names": WEIGHT_NAMES_28, "minimize": True, "smooth": False},
#     "shade-like-15-modified63-smooth-":      {"label": "SHADE-like-63-płynny", "num_weights": 63, "names": WEIGHT_NAMES_63, "minimize": True, "smooth": True},
#     "shade-like-15-modified63-":             {"label": "SHADE-like-63-bazowy", "num_weights": 63, "names": WEIGHT_NAMES_63, "minimize": True, "smooth": False},
# }

# -----------------------------------------------------------------------

PHASE_MIN_SHIFT = -0.1
PHASE_MAX_SHIFT =  0.1

def clamp01(v):
    return max(0.0, min(1.0, v))

def decode_smooth_weights(genes):
    N = 21
    decoded = [0.0] * 63
    for i in range(N):
        p1 = clamp01(genes[i])
        p2 = clamp01(p1 + (-0.1 + genes[N     + i] * 0.2))
        p3 = clamp01(p2 + (-0.1 + genes[2 * N + i] * 0.2))
        decoded[i]         = p1
        decoded[N     + i] = p2
        decoded[2 * N + i] = p3
    return decoded


def parse_last_gen_all(fpath, num_weights, minimize, smooth):
    rows = []
    with open(fpath, "r", encoding="utf-8") as f:
        for line in f:
            line    = line.strip()
            header  = re.match(r'^\s*(\d+)\s*,\s*(\d+)\s*,\s*([-\d.]+)\s*,', line)
            bracket = re.search(r'\[([^\]]+)\]', line)
            if header and bracket:
                gen     = int(header.group(1))
                fitness = float(header.group(3))
                weights = [float(x.strip()) for x in bracket.group(1).split(",") if x.strip()][:num_weights]
                if len(weights) == num_weights:
                    rows.append((gen, fitness, weights))

    if not rows:
        return [], []
    last_gen = max(r[0] for r in rows)
    last     = [(r[1], r[2]) for r in rows if r[0] == last_gen]
    fitnesses, weight_vecs = zip(*last)

    if smooth:
        weight_vecs = [decode_smooth_weights(w) for w in weight_vecs]

    return list(fitnesses), list(weight_vecs)


COLORS_K = ["#4878CF", "#6ACC65", "#D65F5F", "#B47CC7", "#F0A830", "#4EAAA0"]

for prefix, meta in VARIANTS.items():
    pattern = os.path.join(RESULTS_DIR, f"{prefix}individuals-file-*.csv")
    files   = sorted(glob.glob(pattern))

    if not files:
        print(f"Brak plików: {prefix}")
        continue
    if len(files) > 1:
        print(f"UWAGA: {len(files)} plików dla '{prefix}' — używam pierwszego")

    fitnesses, weight_vecs = parse_last_gen_all(
        files[0], meta["num_weights"], meta["minimize"], meta["smooth"]
    )

    if len(weight_vecs) < 4:
        print(f"Za mało osobników do klasteryzacji ({len(weight_vecs)}): {prefix}")
        continue

    X = np.array(weight_vecs)
    Z = linkage(X, method="ward")

    # Szukaj optymalnej liczby klastrów kryterium Silhouette (k=2..6)
    best_k, best_score = 2, -1
    for k in range(2, min(7, len(X))):
        labels = fcluster(Z, k, criterion="maxclust")
        score  = silhouette_score(X, labels)
        if score > best_score:
            best_k, best_score = k, score

    labels     = fcluster(Z, best_k, criterion="maxclust")
    leaf_order = dendrogram(Z, no_plot=True)["leaves"]

    fig, ax = plt.subplots(figsize=(12, 5))
    ddata   = dendrogram(Z, ax=ax, leaf_rotation=90, leaf_font_size=7,
                         link_color_func=lambda k: "#aaaaaa")

    # Koloruj etykiety liści według klastra
    for lbl in ax.get_xmajorticklabels():
        try:
            idx = int(lbl.get_text())
            lbl.set_color(COLORS_K[(labels[idx] - 1) % len(COLORS_K)])
        except ValueError:
            pass

    ax.set_title(
        f"Klasteryzacja hierarchiczna (Ward) — {meta['label']}\n"
        f"Optymalna liczba klastrów: {best_k}  |  Silhouette = {best_score:.3f}",
        fontsize=10
    )
    ax.set_ylabel("Odległość euklidesowa (wagi)")
    ax.set_xlabel(f"Osobnicy ostatniej generacji  (n={len(X)})")

    handles = [
        mpatches.Patch(color=COLORS_K[k], label=f"Klaster {k + 1}")
        for k in range(best_k)
    ]
    ax.legend(handles=handles, fontsize=8, loc="upper right")
    ax.grid(axis="y", alpha=0.2, linestyle=":")

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, f"clustering_{prefix.strip('-')}.png")
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Zapisano: {out_path}  (k={best_k}, silhouette={best_score:.3f})")
