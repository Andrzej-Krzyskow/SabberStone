import re
import os
import glob
import pandas as pd

RESULTS_DIR = r"D:\Pics_Movies\vids\PWr\Sem10\magisterka\RESULTS-FROM-PWR"
OUTPUT_DIR  = r"D:\Pics_Movies\vids\PWr\Sem10\magisterka\RESULTS-FROM-PWR\plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def parse_tournament_file(fpath):
    """Parsuje jeden plik wynikowy turnieju → DataFrame z Agent, Wins, Games, Win%"""
    rows = []
    in_summary = False
    with open(fpath, "r", encoding="utf-8") as f:
        for line in f:
            if "AGGREGATED SUMMARY" in line:
                in_summary = True
            if not in_summary:
                continue
            # Linia danych: "AgentName   15974   36000   44.37%"
            m = re.match(r"^(\S+)\s+(\d+)\s+(\d+)\s+([\d.]+)%", line.strip())
            if m:
                rows.append({
                    "Agent": m.group(1),
                    "Wygrane": int(m.group(2)),
                    "Gry":     int(m.group(3)),
                    "Win%":    float(m.group(4))
                })
    return pd.DataFrame(rows)

# Parsuj wszystkie pliki turniejów
pattern = os.path.join(RESULTS_DIR, "**", "results_*.txt")
files = sorted(glob.glob(pattern, recursive=True))

print(f"Znaleziono {len(files)} plików turniejów:")
for fpath in files:
    print(f"\n=== {os.path.basename(fpath)} ===")
    df = parse_tournament_file(fpath)
    print(df.to_string(index=False))
    # Zapisz CSV obok pliku txt
    csv_path = fpath.replace(".txt", "_parsed.csv")
    df.to_csv(csv_path, index=False)
    print(f"  → {csv_path}")
