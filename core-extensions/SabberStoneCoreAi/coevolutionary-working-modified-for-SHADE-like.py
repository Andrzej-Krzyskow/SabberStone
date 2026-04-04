from random import randint
import time
import os
import subprocess
import threading
import sys

import numpy as np

from shade import improve

DEBUG = True
DECKS = ["RenoKazakusMage", "MidrangeJadeShaman", "AggroPirateWarrior"]
HERO_BY_DECK = {"RenoKazakusMage": "MAGE", "MidrangeJadeShaman": "SHAMAN", "AggroPirateWarrior": "WARRIOR"}
NUM_GAMES = 1  # 20
POP_SIZE = 2  # 10
MAX_EVALUATIONS = 6  # 1000
NUM_THREADS = 12  # 8
NUM_WEIGHTS = 21  # set to 63 when ready
TEMP_FILE_NAME = "results.tmp"
TEST_DUMMY = False

lock = threading.Lock()

victories = []
victories_versus = []
turns_win = []
turns_lose = []
health_win = []
health_lose = []


class Command(object):
	def __init__(self, cmd):
		self.cmd = cmd
		self.process = None

	def run(self, timeout):
		def target():
			self.process = subprocess.Popen(self.cmd, shell=True)
			self.process.communicate()

		thread = threading.Thread(target=target)
		thread.start()
		thread.join(timeout)
		if thread.is_alive():
			print('Terminating process')
			if self.process:
				subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.process.pid)])
			thread.join()
			print("Game lasted a lot :/")
			return False
		return True


def chunks(l, n):
	for i in range(0, len(l), n):
		yield l[i:i + n]


def print_squared_array(the_array):
	l = ""
	for i in range(len(the_array)):
		total = 0
		for j in range(len(the_array)):
			if isinstance(the_array[i][j], float):
				v = "{0:.2f}".format(the_array[i][j])
			else:
				v = str(the_array[i][j])
			l = l + v + " "
			total += the_array[i][j]
		l = l + " TOTAL: " + str(total) + "\n"
	return l


def individual_to_commandline(ind):
	return "#".join(str(e) for e in ind)


def parse_file(file_name):
	print("PARSING FILE " + file_name)
	with open(file_name, "r") as fp:
		lines = fp.readlines()
	match_info = list(filter(None, lines[-1].split(" ")))
	return (int(match_info[0]), int(match_info[1]), int(match_info[3]),
			int(match_info[4]), int(match_info[5]), int(match_info[6]))


def launch_simulator(f1, f2, d1, d2, thread_id):
	file_name = thread_id + TEMP_FILE_NAME

	if os.path.exists(file_name):
		try:
			os.remove(file_name)
		except OSError as e:
			print("Error deleting file " + file_name + ": " + str(e))

	cml1 = individual_to_commandline(f1)
	cml2 = individual_to_commandline(f2)

	if TEST_DUMMY:
		w = randint(0, NUM_GAMES)
		w1, w2 = w, NUM_GAMES - w
		tw = randint(0, 15 * NUM_GAMES)
		tl = randint(0, 15 * NUM_GAMES)
		hw = randint(0, 5 * NUM_GAMES)
		hl = randint(0, 5 * NUM_GAMES)
		command_line = "echo {0} {1} {2} {3} {4} {5} {6} > {7}".format(
			w1, w2, NUM_GAMES, tw, tl, hw, hl, file_name)
	else:
		command_line = (
			r"dotnet run --project D:\Pics_Movies\vids\PWr\Sem10\magisterka\PARALLEL_HS\SabberStone"
			+ thread_id
			+ r"\core-extensions\SabberStoneCoreAi\SabberStoneCoreAi.csproj"
		)
		command_line += " {0} {1} {2} {3} {4} {5} {6} {7}".format(
			d1, HERO_BY_DECK[d1], cml1, d2, HERO_BY_DECK[d2], cml2, NUM_GAMES, " > " + file_name)

	if DEBUG:
		print("\t\t" + command_line)
	com = Command(command_line)

	attempts = 0
	finished = False
	while not finished:
		print("Launching attempt " + str(attempts))
		finished = com.run(100)
		attempts += 1
		if attempts == 3:
			finished = True

	if DEBUG:
		print(str(thread_id) + " finished command launch")

	w1, w2, tw, tl, hw, hl = parse_file(file_name)
	if DEBUG:
		print("\t\tNUMBERS ARE " + str(w1) + " " + str(w2))
	return w1, w2, tw, tl, hw, hl


def execute_simulator_in_thread(battle):
	thread_name = threading.current_thread().name
	print(thread_name + " STARTING ")

	global victories, victories_versus, turns_win, turns_lose, health_win, health_lose

	id_1, id_2, weights_1, weights_2, deck_1, deck_2 = battle

	v1, v2, tw, tl, hw, hl = launch_simulator(weights_1, weights_2, deck_1, deck_2, thread_name)

	print("STARTING LOCK FOR THREAD " + str(thread_name))
	with lock:
		victories[id_1]["TOTAL"] += v1
		victories[id_1][deck_1 + deck_2] += v1
		victories[id_2]["TOTAL"] += v2
		victories[id_2][deck_2 + deck_1] += v2
		victories_versus[id_1][id_2] += v1
		victories_versus[id_2][id_1] += v2
		turns_win[id_1][id_2] += tw
		turns_win[id_2][id_1] += tl
		turns_lose[id_1][id_2] += tl
		turns_lose[id_2][id_1] += tw
		health_win[id_1][id_2] += hw
		health_win[id_2][id_1] += hl
		health_lose[id_1][id_2] += hl
		health_lose[id_2][id_1] += hw
	print(thread_name + " FINISHING")


def evaluate_hearthstone(candidates):
	"""
	Evaluates all candidates against each other (round-robin within the given batch).
	Called by SHADE's improve() as:
		fun(population.tolist())   -- initial evaluation
		fun(u.tolist())            -- trial population evaluation each generation

	candidates: list of lists, shape (n, NUM_WEIGHTS)
	returns:    np.array of shape (n,), negated wins (SHADE minimizes)
	"""
	global victories, victories_versus, turns_win, turns_lose, health_win, health_lose

	to_fight = [list(ind) for ind in candidates]
	n = len(to_fight)

	victories = []
	victories_versus = []
	turns_win = []
	turns_lose = []
	health_win = []
	health_lose = []

	for i in range(n):
		victories.append({"TOTAL": 0})
		for d1 in DECKS:
			for d2 in DECKS:
				victories[i][d1 + d2] = 0
		victories_versus.append([0] * n)
		turns_win.append([0] * n)
		turns_lose.append([0] * n)
		health_win.append([0] * n)
		health_lose.append([0] * n)

	battles_list = []
	for i, f1 in enumerate(to_fight):
		if DEBUG:
			print("INDIVIDUAL " + str(i) + ": " + str(f1))
		for j, f2 in enumerate(to_fight):
			for d1 in DECKS:
				for d2 in DECKS:
					if i < j:
						battles_list.append([i, j, f1, f2, d1, d2])

	for parallel_battle in chunks(battles_list, NUM_THREADS):
		threads = []
		if DEBUG:
			print("EXECUTING PARALLEL BATTLES: " + str(len(parallel_battle)))
		for i, battle in enumerate(parallel_battle):
			t = threading.Thread(target=execute_simulator_in_thread, args=(battle,), name=str(i))
			threads.append(t)
		for t in threads:
			t.start()
		for t in threads:
			t.join()

	fitness = []
	for i in range(n):
		# SHADE minimizes — negate wins so more wins = lower (better) value
		fitness.append(-float(victories[i]["TOTAL"]))

	if DEBUG:
		print("VICTORIES (batch)")
		print(print_squared_array(victories_versus))

		for i in range(n):
			for j in range(n):
				if i != j:
					ij = float(victories_versus[i][j])
					ji = float(victories_versus[j][i])
					if ij > 0:
						turns_win[i][j] /= ij
						health_win[i][j] /= ij
					if ji > 0:
						turns_lose[i][j] /= ji
						health_lose[i][j] /= ji

		print("TURNS TO WIN")
		print(print_squared_array(turns_win))
		print("TURNS TO LOSE")
		print(print_squared_array(turns_lose))
		print("HEALTH TO WIN")
		print(print_squared_array(health_win))
		print("HEALTH TO LOSE")
		print(print_squared_array(health_lose))

	return np.array(fitness)


def run_one():
	time1 = time.time()

	# --- initial population: shape (POP_SIZE, NUM_WEIGHTS), values in [0, 1] ---
	population = np.random.uniform(0.0, 1.0, size=(POP_SIZE, NUM_WEIGHTS))

	# --- evaluate initial population fitness ---
	# passing population_fitness to improve() skips re-evaluation inside SHADE
	population_fitness = evaluate_hearthstone(population.tolist())

	# --- SHADE run_info ---
	# 'best' is the theoretical optimum used only for logging the gap.
	# We don't have a known optimum, so set to -inf (gap will be large but harmless).
	# 'threshold' is a stopping criterion; set to -inf to disable it.
	run_info = {
		'lower': 0.0,
		'upper': 1.0,
		'threshold': -np.inf,
		'best': -np.inf,
	}

	result, best_idx = improve(
		fun=evaluate_hearthstone,  # called as fun(candidates_list) -> np.array of fitness
		run_info=run_info,
		dimension=NUM_WEIGHTS,
		check_evals=MAX_EVALUATIONS,
		popsize=POP_SIZE,
		population=population,
		population_fitness=population_fitness,  # skip re-evaluation of gen 0
	)

	time2 = time.time()
	print("TIME ELAPSED = " + str(time2 - time1))
	print("Best fitness (negated wins): {:.4f}".format(result.fitness))
	print("Best weights: " + str(result.solution))
	return result


def main():
	for _ in range(1):
		run_one()


if __name__ == '__main__':
	main()
