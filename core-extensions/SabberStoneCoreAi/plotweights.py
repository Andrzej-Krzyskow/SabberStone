import csv
import os

import pandas as pd

directory = r"D:\Pics_Movies\vids\PWr\Sem10\magisterka\SabberStone\core-extensions\SabberStoneCoreAi\results\victories\\"
files = []

for fname in os.listdir(directory):
	if fname.startswith("inspyred-individuals"):
		files.append(directory + fname)

df_weights = pd.DataFrame(
	columns=("HHR", "HAR", "BMHR", "BMAR", "BMA", "BMK", "BSR", "BMR", "MH", "MA", "MHC", "MHD", "MHDS", "MHI", "MHLS",
			 "MHS", "MHT", "MHW", "MR", "MM", "MHP"))

for f, filename in enumerate(files):
	print("Reading file ") + filename
	with open(filename, 'rb') as f:
		reader = csv.reader(f)
		for row in reader:
			# print row
			if row[0] == "99":
				# print "LAST LINE"
				# print row
				values = []
				for j in range(21):
					v = row[j + 3]
					v = v.replace("[", "")
					v = float(v)
					values.append(v)
				# print values
				df_weights.loc[len(df_weights)] = values

print(df_weights)

"""axes_battlefield = df_weights.boxplot(column=["HHR", "HAR", "BMHR", "BMAR", "BMA", "BMK", "BSR", "BMR"])
axes_battlefield.set_ylabel("Weight")
fig_battlefield = axes_battlefield.get_figure()
fig_battlefield.savefig("weights_battlefield.png",dpi=1200)"""

axes_minions = df_weights.boxplot(
	column=["MH", "MA", "MHC", "MHD", "MHDS", "MHI", "MHLS", "MHS", "MHT", "MHW", "MHP", "MR",
			"MM"])  # MHP has changed the position!
axes_minions.set_ylabel("Weight")
fig_minions = axes_minions.get_figure()
fig_minions.savefig("weights_minions.png", dpi=1200)
