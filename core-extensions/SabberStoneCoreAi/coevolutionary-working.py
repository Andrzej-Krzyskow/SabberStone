from random import Random
import time
import inspyred

DECKS = ["RenoKazakusMage", "MidrangeJadeShaman", "AggroPirateWarrior"]
HERO_BY_DECK = {"RenoKazakusMage": "MAGE", "MidrangeJadeShaman": "SHAMAN", "AggroPirateWarrior": "WARRIOR"}
NUM_GAMES = 20
POP_SIZE = 10
MAX_EVALUATIONS = 1000
NUM_WEIGHTS = 21

dotnet_run_counter = 0


def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def generate_weights(random, args):
    size = args.get('num_weights')
    return [random.uniform(0, 1) for i in range(size)]


def launch_simulator(f1, f2, d1, d2, thread_id):
    global dotnet_run_counter
    dotnet_run_counter += 1
    return NUM_GAMES // 2, NUM_GAMES - NUM_GAMES // 2, 0, 0, 0, 0


def evaluate_hearthstone(candidates, args):
    parents = args['_ec'].population
    to_fight = [p.candidate[:len(p.candidate) // 2] for p in parents]
    num_parents = len(parents)
    to_fight = to_fight + candidates

    victories = [{"TOTAL": 0, **{d1 + d2: 0 for d1 in DECKS for d2 in DECKS}} for _ in to_fight]
    victories_versus = [[0] * len(to_fight) for _ in to_fight]

    battles_list = [
        [i, j, f1, f2, d1, d2]
        for i, f1 in enumerate(to_fight)
        for j, f2 in enumerate(to_fight)
        for d1 in DECKS
        for d2 in DECKS
        if i < j
    ]

    for battle in battles_list:
        id_1, id_2, w1, w2, deck_1, deck_2 = battle[0], battle[1], battle[2], battle[3], battle[4], battle[5]
        v1, v2, *_ = launch_simulator(w1, w2, deck_1, deck_2, f"{id_1}_{id_2}")
        victories[id_1]["TOTAL"] += v1
        victories[id_1][deck_1 + deck_2] += v1
        victories[id_2]["TOTAL"] += v2
        victories[id_2][deck_2 + deck_1] += v2
        victories_versus[id_1][id_2] += v1
        victories_versus[id_2][id_1] += v2

    fitness = []
    for i, v in enumerate(victories):
        if i < num_parents:
            args["_ec"].population[i].fitness = v["TOTAL"]
        else:
            fitness.append(v["TOTAL"])

    return fitness


def run_one(prng=None, display=False):
    if prng is None:
        prng = Random()
        prng.seed(time.time())

    ea = inspyred.ec.ES(prng)
    ea.terminator = [inspyred.ec.terminators.evaluation_termination]
    final_pop = ea.evolve(
        generator=generate_weights,
        num_weights=NUM_WEIGHTS,
        evaluator=evaluate_hearthstone,
        pop_size=POP_SIZE,
        bounder=inspyred.ec.Bounder(0, 1),
        maximize=True,
        max_evaluations=MAX_EVALUATIONS
    )

    print(f"TOTAL dotnet run invocations: {dotnet_run_counter}")
    return ea


def main(prng=None, display=False):
    run_one(prng, display)


if __name__ == '__main__':
    main()
