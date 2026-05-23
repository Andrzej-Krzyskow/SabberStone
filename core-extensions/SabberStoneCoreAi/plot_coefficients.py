import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import glob

RESULTS_DIR = r"D:\Pics_Movies\vids\PWr\Sem10\magisterka\SabberStone\core-extensions\SabberStoneCoreAi\analysis\results"
OUTPUT_DIR = r"D:\Pics_Movies\vids\PWr\Sem10\magisterka\SabberStone\core-extensions\SabberStoneCoreAi\analysis\plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SHADE_VARIANTS = {
    "shade-pure-15-":                        "SHADE-pure-21",
    "shade-like-15-":                        "SHADE-like-21",
    "shade-like-15-modified28-":             "SHADE-like-28",
    "shade-like-15-modified28-normalized-":  "SHADE-like-28-norm",
    "shade-like-15-modified63-smooth-":      "SHADE-like-63-płynny",
    "shade-like-15-modified63-":             "SHADE-like-63-bazowy",
}

fig, (ax_f, ax_cr) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
fig.suptitle("Adaptacja parametrów SHADE: F (skala mutacji) i CR (crossover rate)", fontsize=12)

COLORS = ["#4878CF","#6ACC65","#D65F5F","#B47CC7","#F0A830","#4EAAA0"]

for i, (prefix, label) in enumerate(SHADE_VARIANTS.items()):
    pattern = os.path.join(RESULTS_DIR, f"{prefix}coefficients-file-*.csv")
    files   = sorted(glob.glob(pattern))
    if not files:
        continue
    df = pd.read_csv(files[0], skipinitialspace=True)
    c  = COLORS[i % len(COLORS)]
    ax_f.plot(df["generation"],  df["mean_f"],  label=label, color=c, linewidth=1.8)
    ax_cr.plot(df["generation"], df["mean_cr"], label=label, color=c, linewidth=1.8)

for ax, name, ref in [(ax_f, "mean F (skala mutacji)", 0.5),
                      (ax_cr, "mean CR (crossover rate)", 0.5)]:
    ax.axhline(ref, color="gray", linestyle="--", alpha=0.5, linewidth=1, label="start (0.5)")
    ax.set_ylabel(name)
    ax.grid(alpha=0.25, linestyle=":")
    ax.legend(fontsize=7, loc="upper left")

ax_cr.set_xlabel("Generacja")
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "shade_coefficients.png"), dpi=150)
plt.close()
print("Zapisano shade_coefficients.png")
