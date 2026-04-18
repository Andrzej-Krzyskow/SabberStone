"""
Path A: pure-SHADE Hearthstone optimizer with Hall of Fame.

Hall of Fame mechanism:
  Every HOF_UPDATE_INTERVAL generations:
    1. Find the best individual in the current population.
    2. Find the WORST opponent in FIXED_OPPONENTS (lowest avg wins against the population)
       and replace it with the current best individual.
    3. Save the updated opponent list back to OPPONENTS_CSV.
    4. Re-evaluate ALL parents against the new opponent set so the upcoming
       mutant comparisons are on the same scale.

Opponent CSV format (one opponent per line, NUM_WEIGHTS comma-separated floats):
    0.12,0.55,0.31,...

Bootstrap: run the coevolutionary version first, take 15 best individuals from
shade-individuals-file-*.csv and paste them into opponents.csv.
"""
import shutil
import sys
from random import randint
import time
import os
import subprocess
import threading

improve = __import__("shade-modified").improve

import numpy as np

DEBUG = True
DECKS = ["RenoKazakusMage", "MidrangeJadeShaman", "AggroPirateWarrior"]
HERO_BY_DECK = {"RenoKazakusMage": "MAGE", "MidrangeJadeShaman": "SHAMAN", "AggroPirateWarrior": "WARRIOR"}
NUM_GAMES = 20 #8
POP_SIZE = 5 #10
MAX_EVALUATIONS = 1745 #1000
NUM_THREADS = 128  # 8
NUM_WEIGHTS = 21
TEMP_FILE_NAME = "results.tmp"
TEST_DUMMY = False

OPPONENTS_CSV_ORIGINAL = "opponents-5.csv"
HOF_UPDATE_INTERVAL = 5  # replace one opponent every N generations

lock = threading.Lock()

FIXED_OPPONENTS = []  # list of lists, shape (N_opp, NUM_WEIGHTS)


# ---------------------------------------------------------------------------
# Opponent I/O
# ---------------------------------------------------------------------------

def load_opponents(csv_path):
	opponents = []
	with open(csv_path, "r") as f:
		for line in f:
			line = line.strip()
			if not line or line.startswith("#"):
				continue
			weights = [float(x) for x in line.split(",")]
			assert len(weights) == NUM_WEIGHTS, \
				"Opponent row has {} weights, expected {}".format(len(weights), NUM_WEIGHTS)
			opponents.append(weights)
	assert len(opponents) > 0, "opponents.csv is empty: " + csv_path
	print("Loaded {} fixed opponents from {}".format(len(opponents), csv_path))
	return opponents


def save_opponents(opponents, csv_path):
	with open(csv_path, "w") as f:
		for w in opponents:
			f.write(",".join("{:.16f}".format(x) for x in w) + "\n")
	print("[HOF] Saved {} opponents to {}".format(len(opponents), csv_path))


# ---------------------------------------------------------------------------
# Simulator boilerplate
# ---------------------------------------------------------------------------

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


def print_opponent_array(wins_matrix):
	"""wins_matrix[i][j] = wins of individual i vs opponent j"""
	l = ""
	for i in range(len(wins_matrix)):
		total = sum(wins_matrix[i])
		row = "  ".join(str(v) for v in wins_matrix[i])
		l += "ind {}: {}  TOTAL: {}\n".format(i, row, total)
	return l


def individual_to_commandline(ind):
	return "#".join(str(e) for e in ind)


def parse_file(file_name):
	print("PARSING FILE " + file_name)
	with open(file_name, "r") as fp:
		lines = fp.readlines()
	m = list(filter(None, lines[-1].split(" ")))
	return int(m[0]), int(m[1]), int(m[3]), int(m[4]), int(m[5]), int(m[6])


def launch_simulator(f1, f2, d1, d2, thread_id):
	file_name = thread_id + TEMP_FILE_NAME
	if os.path.exists(file_name):
		try:
			os.remove(file_name)
		except OSError as e:
			print("Error deleting file {}: {}".format(file_name, e))

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
		# 1. Get the base directory (works for both .py scripts and the final .exe)
		if getattr(sys, 'frozen', False):
			base_dir = os.path.dirname(sys.executable)
		else:
			base_dir = os.path.dirname(os.path.abspath(__file__))
		project_path = os.path.join(
			base_dir,
			"PARALLEL_HS",
			f"SabberStone{thread_id}",
			"core-extensions",
			"SabberStoneCoreAi",
			"SabberStoneCoreAi.csproj"
		)

		# 3. Construct the command line with quotes around the path
		command_line = f'dotnet run --project "{project_path}"'
		command_line += " {0} {1} {2} {3} {4} {5} {6} {7}".format(d1, HERO_BY_DECK[d1], cml1, d2, HERO_BY_DECK[d2],
												  cml2, NUM_GAMES, " > " + file_name)

	if DEBUG:
		print("\t\t" + command_line)
	com = Command(command_line)

	attempts, finished = 0, False
	while not finished:
		print("Launching attempt " + str(attempts))
		finished = com.run(100)
		attempts += 1
		if attempts == 3:
			finished = True

	w1, w2, tw, tl, hw, hl = parse_file(file_name)
	if DEBUG:
		print("\t\tNUMBERS ARE {} {}".format(w1, w2))
	return w1, w2, tw, tl, hw, hl


# ---------------------------------------------------------------------------
# Core evaluation — single individual vs FIXED_OPPONENTS
# ---------------------------------------------------------------------------

_eval_wins_per_opponent = []
_eval_lock = threading.Lock()


def _battle_vs_fixed_opponent(individual_weights, opp_idx, opp_weights, d1, d2):
	thread_name = threading.current_thread().name
	v1, _v2, _tw, _tl, _hw, _hl = launch_simulator(
		individual_weights, opp_weights, d1, d2, thread_name)
	with _eval_lock:
		_eval_wins_per_opponent[opp_idx] += v1


def evaluate_hearthstone(individual):
	"""
	Evaluate a SINGLE individual against all FIXED_OPPONENTS (all deck combos).
	Returns: -total_wins  (negated so SHADE minimizes = maximize wins)
	Side-effect: updates _eval_wins_per_opponent for the observer/tracker.
	"""
	global _eval_wins_per_opponent

	weights = list(individual)
	n_opp = len(FIXED_OPPONENTS)
	_eval_wins_per_opponent = [0] * n_opp

	battles = []
	for opp_idx, opp_weights in enumerate(FIXED_OPPONENTS):
		for d1 in DECKS:
			for d2 in DECKS:
				battles.append((weights, opp_idx, opp_weights, d1, d2))

	for chunk in chunks(battles, NUM_THREADS):
		threads = []
		for i, (w, opp_idx, opp_w, d1, d2) in enumerate(chunk):
			t = threading.Thread(
				target=_battle_vs_fixed_opponent,
				args=(w, opp_idx, opp_w, d1, d2),
				name=str(i))
			threads.append(t)
		for t in threads:
			t.start()
		for t in threads:
			t.join()

	total_wins = sum(_eval_wins_per_opponent)
	if DEBUG:
		print("  eval: wins_per_opp={}, total={}".format(_eval_wins_per_opponent, total_wins))

	return -float(total_wins)


# ---------------------------------------------------------------------------
# Tracking wrapper for logging (captures per-opponent detail)
# ---------------------------------------------------------------------------

_last_wins_per_opponent = {}  # {ind_idx_in_generation: [wins_vs_opp0, ...]}
_current_eval_idx = [0]  # mutable counter, reset each generation by observer


def evaluate_hearthstone_tracked(individual):
	"""Wrapper: evaluates and captures per-opponent wins keyed by call order."""
	result = evaluate_hearthstone(individual)
	idx = _current_eval_idx[0]
	_last_wins_per_opponent[idx] = list(_eval_wins_per_opponent)
	_current_eval_idx[0] += 1
	return result


# ---------------------------------------------------------------------------
# Hall of Fame update function
# ---------------------------------------------------------------------------

def hof_update(population, population_fitness, run_opponents_csv):
    global FIXED_OPPONENTS

    best_idx = int(np.argmin(population_fitness))
    best_weights = population[best_idx].tolist()
    print("[HOF] Best individual idx={}, fitness={:.4f}".format(best_idx, population_fitness[best_idx]))

    n_opp = len(FIXED_OPPONENTS)
    opp_total_wins_against = [0] * n_opp

    for i, wins_list in _last_wins_per_opponent.items():
        for j, w in enumerate(wins_list):
            opp_total_wins_against[j] += w

    worst_opp_idx = int(np.argmax(opp_total_wins_against))
    print("[HOF] Replacing opponent {} (beaten {} times) with current best individual".format(
        worst_opp_idx, opp_total_wins_against[worst_opp_idx]))

    FIXED_OPPONENTS[worst_opp_idx] = best_weights
    save_opponents(FIXED_OPPONENTS, run_opponents_csv)   # ← use the run-local path

    print("[HOF] Re-evaluating all {} parents against updated opponents...".format(len(population)))
    new_fitness = np.array([
        evaluate_hearthstone_tracked(ind) for ind in population.tolist()
    ])

    return new_fitness


# ---------------------------------------------------------------------------
# File observer
# ---------------------------------------------------------------------------

_log_files = {}
_init_time = None


def shade_observer(generation, population, population_fitness, mean_f=0.5, mean_cr=0.5):
	global _log_files, _init_time, _current_eval_idx

	if generation == 0:
		_init_time = time.time()
		ts = time.strftime('%m%d%Y-%H%M%S')
		_log_files['stats'] = open('shade-pure-5-statistics-file-{}.csv'.format(ts), 'w')
		_log_files['indiv'] = open('shade-pure-5-individuals-file-{}.csv'.format(ts), 'w')
		_log_files['matrix'] = open('shade-pure-5-matrix-file-{}.csv'.format(ts), 'w')
		_log_files['coeff'] = open('shade-pure-5-coefficients-file-{}.csv'.format(ts), 'w')
		_log_files['matrix'].write("# generation | ind | opp0 opp1 ... oppN\n")
		_log_files['coeff'].write("generation, mean_f, mean_cr\n")
		for f in _log_files.values():
			f.flush()

	# Reset eval tracker for next generation
	_current_eval_idx[0] = 0

	stats_f = _log_files['stats']
	indiv_f = _log_files['indiv']
	matrix_f = _log_files['matrix']
	coeff_f = _log_files['coeff']

	elapsed = time.time() - _init_time
	n = len(population_fitness)

	# --- statistics ---
	worst = float(np.max(population_fitness))
	best = float(np.min(population_fitness))
	avg = float(np.mean(population_fitness))
	med = float(np.median(population_fitness))
	std = float(np.std(population_fitness))
	stats_f.write('{}, {}, {}, {}, {}, {}, {}, {}\n'.format(
		generation, n, worst, best, med, avg, std, elapsed))
	stats_f.flush()

	# --- individuals ---
	for i, (weights, fit) in enumerate(zip(population, population_fitness)):
		wins_detail = _last_wins_per_opponent.get(i, [])
		wins_str = ",".join(str(w) for w in wins_detail)
		total_wins = -int(fit)
		indiv_f.write('{}, {}, {}, {}, TOTAL_WINS: {}, WINS_PER_OPP: {}\n'.format(
			generation, i, fit, list(weights), total_wins, wins_str))
	indiv_f.flush()

	# --- matrix ---
	matrix_f.write("generation {}\n".format(generation))
	for i in range(n):
		wins_per_opp = _last_wins_per_opponent.get(i, ["?"] * len(FIXED_OPPONENTS))
		row = "  ind {}: {}".format(i, "  ".join(
			"opp{}={}".format(j, w) for j, w in enumerate(wins_per_opp)))
		matrix_f.write(row + "\n")
	matrix_f.write("\n")
	matrix_f.flush()

	# --- coefficients ---
	coeff_f.write("{}, {:.4f}, {:.4f}\n".format(generation, mean_f, mean_cr))
	coeff_f.flush()


# ---------------------------------------------------------------------------
# Main run
# ---------------------------------------------------------------------------

def run_one():
    global FIXED_OPPONENTS

    # ── Snapshot opponents.csv so every run starts from the same baseline ──
    ts = time.strftime('%m%d%Y-%H%M%S')
    run_opponents_csv = "opponents-{}.csv".format(ts)
    shutil.copy2(OPPONENTS_CSV_ORIGINAL, run_opponents_csv)
    print("[INIT] Copied {} → {}".format(OPPONENTS_CSV_ORIGINAL, run_opponents_csv))

    FIXED_OPPONENTS = load_opponents(run_opponents_csv)

    time1 = time.time()

    population = np.random.uniform(0.0, 1.0, size=(POP_SIZE, NUM_WEIGHTS))

    population_fitness = np.array([
        evaluate_hearthstone_tracked(ind) for ind in population.tolist()
    ])

    run_info = {
        'lower': 0.0,
        'upper': 1.0,
        'threshold': -np.inf,
        'best': -np.inf,
    }

    result, best_idx = improve(
        fun=evaluate_hearthstone_tracked,
        run_info=run_info,
        dimension=NUM_WEIGHTS,
        check_evals=MAX_EVALUATIONS,
        popsize=POP_SIZE,
        population=population,
        population_fitness=population_fitness,
        observer=shade_observer,
        H=POP_SIZE,
        hof_update_fn=hof_update,
        hof_interval=HOF_UPDATE_INTERVAL,
        run_opponents_csv=run_opponents_csv,   # ← pass the path through
    )

    for f in _log_files.values():
        f.close()

    time2 = time.time()
    print("TIME ELAPSED = {:.1f}s".format(time2 - time1))
    print("Best fitness (negated wins): {:.4f}".format(result.fitness))
    print("Best weights: " + str(result.solution.tolist()))

    save_opponents([result.solution.tolist()], "best_solution-{}.csv".format(ts))

    return result


def main():
	run_one()


if __name__ == '__main__':
	main()
