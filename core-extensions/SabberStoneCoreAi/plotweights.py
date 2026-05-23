import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os
import glob
import re

RESULTS_DIR = r"D:\Pics_Movies\vids\PWr\Sem10\magisterka\SabberStone\core-extensions\SabberStoneCoreAi\analysis\results"
OUTPUT_DIR  = r"D:\Pics_Movies\vids\PWr\Sem10\magisterka\SabberStone\core-extensions\SabberStoneCoreAi\analysis\plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

WEIGHT_NAMES_21 = [
	"HHR","HAR","BMHR","BMAR","BMA","BMK","BSR","BMR",
	"MH","MA","MHC","MHD","MHDS","MHI","MHLS","MHS","MHT","MHW","MR","MM","MHP"
]
WEIGHT_NAMES_28 = WEIGHT_NAMES_21 + ["Br","Ręka","Zak","Prz","Smok","Jade","Pir"]
# Trzy zestawy po 21 wag — każdy zestaw z sufiksem _1, _2, _3
WEIGHT_NAMES_63 = (
	[f"{n}_1" for n in WEIGHT_NAMES_21] +  # wagi 1–21
	[f"{n}_2" for n in WEIGHT_NAMES_21] +  # wagi 22–42
	[f"{n}_3" for n in WEIGHT_NAMES_21]    # wagi 43–63
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
#     "shade-like-15-":                        {"label": "21-shade",        "num_weights": 21, "names": WEIGHT_NAMES_21, "minimize": True, "smooth": False},
#     "shade-like-15-modified28-":             {"label": "28-shade",        "num_weights": 28, "names": WEIGHT_NAMES_28, "minimize": True, "smooth": False},
#     "shade-like-15-modified28-normalized-":  {"label": "28-shade-norm",   "num_weights": 28, "names": WEIGHT_NAMES_28, "minimize": True, "smooth": False},
#     "shade-like-15-modified63-smooth-":      {"label": "63-shade-płynny", "num_weights": 63, "names": WEIGHT_NAMES_63, "minimize": True, "smooth": True},
#     "shade-like-15-modified63-":             {"label": "63-shade-bazowy", "num_weights": 63, "names": WEIGHT_NAMES_63, "minimize": True, "smooth": False},
# }

# -----------------------------------------------------------------------
# Grupy kolorystyczne słupków
# -----------------------------------------------------------------------
# -----------------------------------------------------------------------
# Grupy kolorystyczne słupków
# Wariant 21/28: Hero + Board + Minion (+ Extra dla dodatkowych 7 wag)
# Wariant 63:    3 zestawy po 21 wag — każdy zestaw inny kolor
# -----------------------------------------------------------------------
GROUPS_21_28 = {
	"Hero":   {"indices": range(0,  2),  "color": "#4878CF"},
	"Board":  {"indices": range(2,  8),  "color": "#6ACC65"},
	"Minion": {"indices": range(8,  21), "color": "#D65F5F"},
	"Extra":  {"indices": range(21, 28), "color": "#B47CC7"},
}

GROUPS_63 = {
	"Zestaw 1 (wagi 1–21)":  {"indices": range(0,  21), "color": "#4878CF"},
	"Zestaw 2 (wagi 22–42)": {"indices": range(21, 42), "color": "#6ACC65"},
	"Zestaw 3 (wagi 43–63)": {"indices": range(42, 63), "color": "#D65F5F"},
}


def get_color_for_index(i, num_weights):
	groups = GROUPS_63 if num_weights == 63 else GROUPS_21_28
	for group in groups.values():
		if i in group["indices"]:
			return group["color"]
	return "steelblue"

PHASE_MIN_SHIFT = -0.1
PHASE_MAX_SHIFT =  0.1

def clamp01(v):
	return max(0.0, min(1.0, v))

def decode_shift(gene, min_shift, max_shift):
	return min_shift + gene * (max_shift - min_shift)

def decode_smooth_weights(genes):
	"""
	Replikacja DecodeSmoothWeights z C#.
	Wejście: 63 surowe geny [0,1]
	Wyjście: 63 zdekodowane wagi — rzeczywiste wartości używane przez agenta
	  decoded[i]      = clamp01(genes[i])                          <- faza 1
	  decoded[21+i]   = clamp01(decoded[i]   + shift(genes[21+i])) <- faza 2
	  decoded[42+i]   = clamp01(decoded[21+i]+ shift(genes[42+i])) <- faza 3
	"""
	N = 21
	decoded = [0.0] * 63
	for i in range(N):
		p1 = clamp01(genes[i])
		p2 = clamp01(p1 + decode_shift(genes[N     + i], PHASE_MIN_SHIFT, PHASE_MAX_SHIFT))
		p3 = clamp01(p2 + decode_shift(genes[2 * N + i], PHASE_MIN_SHIFT, PHASE_MAX_SHIFT))
		decoded[i]          = p1
		decoded[N     + i]  = p2
		decoded[2 * N + i]  = p3
	return decoded


# -----------------------------------------------------------------------

def extract_best_from_file(fpath, num_weights, minimize):
	"""
	Z pojedynczego pliku individuals wyciąga najlepszego osobnika
	z ostatniej generacji.
	"""
	rows = []
	with open(fpath, "r", encoding="utf-8") as f:
		for line in f:
			line = line.strip()
			if not line:
				continue
			header_match  = re.match(r'^\s*(\d+)\s*,\s*(\d+)\s*,\s*([-\d.]+)\s*,', line)
			bracket_match = re.search(r'\[([^\]]+)\]', line)
			if header_match and bracket_match:
				gen     = int(header_match.group(1))
				fitness = float(header_match.group(3))
				inner   = bracket_match.group(1)
				weights = [float(x.strip()) for x in inner.split(",") if x.strip()][:num_weights]
				rows.append((gen, fitness, weights))

	if not rows:
		raise ValueError(f"Nie znaleziono żadnych wierszy w {fpath}")

	last_gen      = max(r[0] for r in rows)
	last_gen_rows = [r for r in rows if r[0] == last_gen]

	best = min(last_gen_rows, key=lambda r: r[1]) if minimize else max(last_gen_rows, key=lambda r: r[1])
	return best[2], best[1]


for prefix, meta in VARIANTS.items():
	pattern = os.path.join(RESULTS_DIR, f"{prefix}individuals-file-*.csv")
	files   = sorted(glob.glob(pattern))

	if not files:
		print(f"Brak plików: {prefix}")
		continue

	if len(files) > 1:
		print(f"UWAGA: znaleziono {len(files)} plików dla '{prefix}' — używam pierwszego: {os.path.basename(files[0])}")

	fpath = files[0]  # zawsze 1 plik na wariant
	source_file = os.path.basename(fpath)

	try:
		weights, fitness = extract_best_from_file(fpath, meta["num_weights"], meta["minimize"])
		if meta.get("smooth", False):
			weights = decode_smooth_weights(weights)
	except Exception as e:
		print(f"BŁĄD {prefix}: {e}")
		continue

	wins = abs(int(fitness))
	print(f"{meta['label']}: fitness={fitness:.0f}, plik: {source_file}")

	names  = meta["names"][:meta["num_weights"]]
	n      = len(names)
	x      = np.arange(n)
	# linia ~kolory
	colors = [get_color_for_index(i, meta["num_weights"]) for i in range(n)]

	fig, ax = plt.subplots(figsize=(max(10, n * 0.55), 5))

	bars = ax.bar(x, weights, color=colors, alpha=0.85, edgecolor="white", linewidth=0.5)

	ax.axhline(0.5, color="gray", linestyle="--", alpha=0.5, linewidth=1, label="w = 0.5")

	# Etykiety tylko dla wag skrajnych (bardzo wysokich lub bardzo niskich)
	for bar, val in zip(bars, weights):
		if val > 0.85 or val < 0.10:
			ax.text(bar.get_x() + bar.get_width() / 2, val + 0.02,
					f"{val:.2f}", ha="center", va="bottom", fontsize=7, color="#333333")

	ax.set_xticks(x)
	ax.set_xticklabels(names, rotation=45, ha="right", fontsize=8.5)
	ax.set_ylim(0, 1.15)
	ax.set_ylabel("Wartość wagi")
	ax.set_title(
		f"Wagi najlepszego osobnika — {meta['label']}\n"
		f"fitness = {wins} wygranych  |  {source_file}",
		fontsize=10
	)
	ax.grid(axis="y", alpha=0.25, linestyle=":")

	groups = GROUPS_63 if meta["num_weights"] == 63 else GROUPS_21_28
	legend_handles = [
		mpatches.Patch(color=g["color"], label=name)
		for name, g in groups.items()
		if any(i in g["indices"] for i in range(n))
	]
	legend_handles.append(plt.Line2D([0], [0], color="gray", linestyle="--", label="w = 0.5"))
	ax.legend(handles=legend_handles, fontsize=8, loc="upper right")

	plt.tight_layout()
	out_path = os.path.join(OUTPUT_DIR, f"weights_{prefix.strip('-')}.png")
	plt.savefig(out_path, dpi=150)
	print(f"  Zapisano: {out_path}")
	plt.close()
