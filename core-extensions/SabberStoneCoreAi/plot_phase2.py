import pandas as pd
import matplotlib.pyplot as plt
import os

OUTPUT_DIR = r"D:\Pics_Movies\vids\PWr\Sem10\magisterka\RESULTS-FROM-PWR\plots"

# Wklej tutaj wyniki z turnieju Fazy II po jego przeprowadzeniu
# (lub wczytaj z CSV wygenerowanego przez skrypt 4)
data = {
    "Agent":   ["21-koew", "28-koew", "28-norm-koew", "63-koew", "63-płynny-koew", "21-depth-koew"],
    "Win%":    [0.0,        0.0,       0.0,             0.0,       0.0,              0.0],   # ← uzupełnij
    "Grupa":   ["21 param", "28 param","28 param",     "63 param","63 param",       "21 param"]
}
df = pd.DataFrame(data).sort_values("Win%", ascending=True)

COLORS = {"21 param": "steelblue", "28 param": "darkorange", "63 param": "seagreen"}
colors = [COLORS[g] for g in df["Grupa"]]

fig, ax = plt.subplots(figsize=(9, 5))
bars = ax.barh(df["Agent"], df["Win%"], color=colors, alpha=0.85, edgecolor="white")
ax.axvline(50, color="gray", linestyle="--", alpha=0.6, label="50% (próg)")
ax.set_xlabel("Win% (turniej główny)")
ax.set_title("Faza II — porównanie wariantów modyfikacji")
ax.set_xlim(0, 100)

# Etykiety wartości
for bar, val in zip(bars, df["Win%"]):
    ax.text(val + 0.5, bar.get_y() + bar.get_height()/2,
            f"{val:.1f}%", va="center", fontsize=9)

# Legenda grup
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor=c, label=g) for g, c in COLORS.items()]
ax.legend(handles=legend_elements, loc="lower right", fontsize=8)
ax.grid(axis="x", alpha=0.3)

plt.tight_layout()
out_path = os.path.join(OUTPUT_DIR, "phase2_comparison.png")
plt.savefig(out_path, dpi=150)
print(f"Zapisano: {out_path}")
plt.close()
