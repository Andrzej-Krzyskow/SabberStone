"""
Path A: pure-SHADE Hearthstone optimizer.
Each individual's fitness = wins against a FIXED set of opponents loaded from CSV.
Fitness is absolute (not relative to current population), so standard SHADE applies directly.

Opponent CSV format (one opponent per line, NUM_WEIGHTS comma-separated floats):
    0.12,0.55,0.31,...
    0.88,0.02,0.77,...

To bootstrap: run the coevolutionary version first, take the best weights from
shade-individuals-file-*.csv and paste them into opponents.csv.
"""
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
NUM_GAMES   = 8    # 20
POP_SIZE    = 8    # 10
MAX_EVALUATIONS = 200    # 1000
NUM_THREADS = 12   # 8
NUM_WEIGHTS = 21   # set to 63 when ready
TEMP_FILE_NAME = "results.tmp"
TEST_DUMMY  = True

OPPONENTS_CSV = "opponents.csv"   # path to fixed opponents file

lock = threading.Lock()

# ---------------------------------------------------------------------------
# Fixed opponents — loaded once at startup
# ---------------------------------------------------------------------------
FIXED_OPPONENTS = []   # list of lists, each inner list has NUM_WEIGHTS floats


def load_opponents(csv_path):
    """Load fixed opponents from CSV. Each row = one opponent's weights."""
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
    assert len(opponents) > 0, "opponents.csv is empty or not found at: " + csv_path
    print("Loaded {} fixed opponents from {}".format(len(opponents), csv_path))
    return opponents

# ---------------------------------------------------------------------------
# Simulator boilerplate (unchanged)
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


def print_squared_array(the_array):
    l = ""
    for i in range(len(the_array)):
        total = 0
        for j in range(len(the_array[i])):
            v = "{0:.2f}".format(the_array[i][j]) if isinstance(the_array[i][j], float) else str(the_array[i][j])
            l += v + " "
            total += the_array[i][j]
        l += " TOTAL: " + str(total) + "\n"
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
# Per-individual evaluation against fixed opponents
# ---------------------------------------------------------------------------

# Thread-local accumulator — reset before each individual evaluation
_eval_wins_per_opponent = []   # list[int], one entry per opponent, filled by threads
_eval_lock = threading.Lock()


def _battle_vs_fixed_opponent(individual_weights, opp_idx, opp_weights, d1, d2):
    """Run one battle: individual vs fixed opponent[opp_idx] with deck pair (d1,d2)."""
    thread_name = threading.current_thread().name
    v1, v2, _tw, _tl, _hw, _hl = launch_simulator(
        individual_weights, opp_weights, d1, d2, thread_name)
    with _eval_lock:
        _eval_wins_per_opponent[opp_idx] += v1


def evaluate_hearthstone(individual):
    """
    Evaluate a SINGLE individual against all fixed opponents (round-robin of decks).
    Called by SHADE as: fun(u[i].tolist()) -> scalar

    Returns: -total_wins  (negated so SHADE minimizes = maximize wins)
    """
    global _eval_wins_per_opponent

    weights = list(individual)
    n_opp = len(FIXED_OPPONENTS)

    _eval_wins_per_opponent = [0] * n_opp

    # Build full battle list: individual vs each opponent, all deck combinations
    battles = []
    for opp_idx, opp_weights in enumerate(FIXED_OPPONENTS):
        for d1 in DECKS:
            for d2 in DECKS:
                battles.append((weights, opp_idx, opp_weights, d1, d2))

    # Execute in parallel chunks
    for chunk in chunks(battles, NUM_THREADS):
        threads = []
        for i, (w, opp_idx, opp_w, d1, d2) in enumerate(chunk):
            t = threading.Thread(
                target=_battle_vs_fixed_opponent,
                args=(w, opp_idx, opp_w, d1, d2),
                name=str(i)
            )
            threads.append(t)
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    total_wins = sum(_eval_wins_per_opponent)
    if DEBUG:
        print("  eval: wins_per_opponent={}, total={}".format(_eval_wins_per_opponent, total_wins))

    return -float(total_wins)   # negate: SHADE minimizes


# ---------------------------------------------------------------------------
# File observer
# ---------------------------------------------------------------------------

_log_files  = {}
_init_time  = None
# Snapshot of last individual evaluation results, set by evaluate_hearthstone_for_logging
_last_wins_per_opponent = {}   # {individual_idx: [wins_vs_opp0, wins_vs_opp1, ...]}


def evaluate_hearthstone_logged(individual, ind_idx):
    """
    Same as evaluate_hearthstone but also records per-opponent wins for logging.
    Used only during observer calls to populate _last_wins_per_opponent.
    NOTE: this is NOT called by SHADE directly — SHADE calls evaluate_hearthstone.
    The observer reads _eval_wins_per_opponent after each SHADE call to u[i].
    """
    result = evaluate_hearthstone(individual)
    _last_wins_per_opponent[ind_idx] = list(_eval_wins_per_opponent)
    return result


# We hook into evaluate_hearthstone to capture per-opponent wins per individual
# by wrapping it with a counter so the observer can log per-opponent detail.
_current_eval_idx = [0]   # mutable counter reset each generation


def evaluate_hearthstone_tracked(individual):
    """
    Wrapper passed to improve() instead of bare evaluate_hearthstone.
    Captures per-opponent wins into _last_wins_per_opponent keyed by call order.
    """
    result = evaluate_hearthstone(individual)
    idx = _current_eval_idx[0]
    _last_wins_per_opponent[idx] = list(_eval_wins_per_opponent)
    _current_eval_idx[0] += 1
    return result


def shade_observer(generation, population, population_fitness):
    """
    Writes 3 log files each generation:
        shade-statistics-file-<ts>.csv   — gen stats
        shade-individuals-file-<ts>.csv  — per-individual weights + wins
        shade-matrix-file-<ts>.csv       — wins per opponent for each individual
    """
    global _log_files, _init_time, _current_eval_idx

    if generation == 0:
        _init_time = time.time()
        ts = time.strftime('%m%d%Y-%H%M%S')
        _log_files['stats']  = open('shade-statistics-file-{}.csv'.format(ts),  'w')
        _log_files['indiv']  = open('shade-individuals-file-{}.csv'.format(ts), 'w')
        _log_files['matrix'] = open('shade-matrix-file-{}.csv'.format(ts),      'w')
        # Write header for matrix file so it's self-documenting
        _log_files['matrix'].write("# generation, individual_idx, wins_vs_opp0, wins_vs_opp1, ...\n")
        _log_files['matrix'].flush()

    # Reset tracked counter for next generation
    _current_eval_idx[0] = 0

    stats_f  = _log_files['stats']
    indiv_f  = _log_files['indiv']
    matrix_f = _log_files['matrix']

    elapsed = time.time() - _init_time
    n = len(population_fitness)

    # --- statistics ---
    worst = float(np.max(population_fitness))
    best  = float(np.min(population_fitness))
    avg   = float(np.mean(population_fitness))
    med   = float(np.median(population_fitness))
    std   = float(np.std(population_fitness))
    stats_f.write('{}, {}, {}, {}, {}, {}, {}, {}\n'.format(
        generation, n, worst, best, med, avg, std, elapsed))
    stats_f.flush()

    # --- individuals ---
    for i, (weights, fit) in enumerate(zip(population, population_fitness)):
        wins_detail = _last_wins_per_opponent.get(i, [])
        wins_str = ",".join(str(w) for w in wins_detail)
        total_wins = -int(fit)   # un-negate for readability
        indiv_f.write('{}, {}, {}, {}, TOTAL_WINS: {}, WINS_PER_OPP: {}\n'.format(
            generation, i, fit, list(weights), total_wins, wins_str))
    indiv_f.flush()

    # --- matrix: wins breakdown vs each fixed opponent ---
    matrix_f.write("generation {}\n".format(generation))
    for i in range(n):
        wins_per_opp = _last_wins_per_opponent.get(i, ["?"] * len(FIXED_OPPONENTS))
        row = "  ind {}: {}".format(i, "  ".join(
            "opp{}={}".format(j, w) for j, w in enumerate(wins_per_opp)))
        matrix_f.write(row + "\n")
    matrix_f.write("\n")
    matrix_f.flush()


# ---------------------------------------------------------------------------
# Main run
# ---------------------------------------------------------------------------

def run_one():
    global FIXED_OPPONENTS

    # Load fixed opponents from CSV
    FIXED_OPPONENTS = load_opponents(OPPONENTS_CSV)

    time1 = time.time()

    population = np.random.uniform(0.0, 1.0, size=(POP_SIZE, NUM_WEIGHTS))

    # Evaluate initial population — each individual independently
    population_fitness = np.array([
        evaluate_hearthstone_tracked(ind) for ind in population.tolist()
    ])

    run_info = {
        'lower': 0.0,
        'upper': 1.0,
        'threshold': -np.inf,
        'best':      -np.inf,   # no known optimum; used only for logging gap
    }

    result, best_idx = improve(
        fun=evaluate_hearthstone_tracked,   # fun(individual) -> scalar
        run_info=run_info,
        dimension=NUM_WEIGHTS,
        check_evals=MAX_EVALUATIONS,
        popsize=POP_SIZE,
        population=population,
        population_fitness=population_fitness,
        observer=shade_observer,
    )

    for f in _log_files.values():
        f.close()

    time2 = time.time()
    print("TIME ELAPSED = {:.1f}s".format(time2 - time1))
    print("Best fitness (negated wins): {:.4f}".format(result.fitness))
    print("Best weights: " + str(result.solution.tolist()))


    return result


def main():
    run_one()


if __name__ == '__main__':
    main()
