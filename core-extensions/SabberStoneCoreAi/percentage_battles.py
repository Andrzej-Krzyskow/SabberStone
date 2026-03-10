import pandas as pd
import matplotlib.pyplot as plt
import csv
import os
import re

directory = r"D:\Pics_Movies\vids\PWr\Sem10\magisterka\SabberStone\core-extensions\SabberStoneCoreAi\results\victories\\"
files = []

for fname in os.listdir(directory):
	if fname.startswith("inspyred-individuals"):
		files.append(directory + fname)

df_battles = pd.DataFrame(columns=("1", "2", "3", "4", "5", "6", "7", "8", "9"))

for f, filename in enumerate(files):
	print("Reading file ") + filename
	with open(filename, 'rb') as f:
		reader = csv.reader(f)
		for row in reader:
			# print row
			if row[0] == "99":
				# print "LAST LINE"
				# print row
				battles = []
				battleStr = row[45]
				battleStr = battleStr[:-1]  # Removes last "-"
				print(battleStr)
				for b in battleStr.split("-"):
					b = re.sub("[^0-9]", "", b)  # Removes all non-numbers
					print(b)
					b = float(b)
					battles.append(b)
				# print values
				df_battles.loc[len(df_battles)] = battles

print(df_battles)
print(df_battles.sum())
