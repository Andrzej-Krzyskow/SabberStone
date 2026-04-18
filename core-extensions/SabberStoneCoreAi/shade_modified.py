"""
SHADE algorithm - Path A (pure SHADE style) with Hall of Fame support.

fun signature:      fun(individual: list) -> float   (scalar, SHADE minimizes)
hof_update_fn:      called every hof_interval generations to swap one opponent
                    and re-evaluate all parents against the new opponent set.
                    signature: hof_update_fn(population, population_fitness)
                               -> np.ndarray (new population_fitness, same shape)

Tanabe, R.; Fukunaga, A., "Success-history based parameter adaptation
for Differential Evolution," Evolutionary Computation (CEC), 2013
"""
import numpy as np
from DE import EAresult, random_population, get_experiments_file, random_indexes
import math


def improve(fun, run_info, dimension, check_evals, name_output=None, replace=True, popsize=100, H=100,
            population=None, population_fitness=None, initial_solution=None, MemF=None, MemCR=None,
            observer=None, hof_update_fn=None, hof_interval=5):
    """
    Parameters
    ----------
    fun            : callable(individual: list) -> float
    observer       : optional callable(generation, population, population_fitness, mean_f, mean_cr)
    hof_update_fn  : optional callable(population: np.ndarray, population_fitness: np.ndarray)
                     -> np.ndarray (updated population_fitness after opponent swap + re-evaluation)
                     Called every hof_interval generations BEFORE mutation of that generation,
                     so mutation uses weights drawn from the already-updated F/CR memory.
    hof_interval   : int, how many generations between Hall of Fame updates (default 5)
    """
    assert isinstance(dimension, int) and dimension > 0

    final, fid = get_experiments_file(name_output, replace)
    if final is not None:
        return final

    for attr in ['lower', 'upper', 'threshold', 'best']:
        assert attr in run_info, "'{}' not in run_info".format(attr)

    if not isinstance(check_evals, list):
        check_evals = [check_evals]

    domain   = (run_info['lower'], run_info['upper'])
    fun_best = run_info['best']
    maxEval  = check_evals[-1]
    check_eval = check_evals.pop()

    if population is None:
        population = random_population(domain, dimension, popsize)
    else:
        popsize = population.shape[0]

    if initial_solution is not None:
        population[0] = initial_solution

    if population_fitness is None:
        population_fitness = np.array([fun(ind) for ind in population.tolist()])
        currentEval = popsize
    else:
        population_fitness = np.array(population_fitness)
        currentEval = 0

    memory     = population.tolist()
    memorySize = popsize * 2

    if MemF is None:
        MemF = np.ones(H) * 0.5
    if MemCR is None:
        MemCR = np.ones(H) * 0.5

    k             = 0
    pmin          = 2.0 / popsize
    generation    = 0
    total_updates = 0

    if observer is not None:
        observer(generation, population.copy(), population_fitness.copy(), 0.5, 0.5)

    while currentEval < maxEval:
        generation += 1

        # ---------------------------------------------------------------
        # Hall of Fame update — swap opponent, then re-evaluate all parents
        # so the upcoming mutant comparison is on the same scale.
        # Done BEFORE mutation so this generation's trials and parents
        # are evaluated against the same opponent set.
        # ---------------------------------------------------------------
        if hof_update_fn is not None and generation % hof_interval == 0:
            print("[HOF] Generation {} — updating opponent pool and re-evaluating parents...".format(generation))
            population_fitness = hof_update_fn(population, population_fitness)
            print("[HOF] Re-evaluation complete. New best fitness: {:.4f}".format(np.min(population_fitness)))

        SCR = []
        SF  = []
        F   = np.zeros(popsize)
        CR  = np.zeros(popsize)
        u   = np.zeros((popsize, dimension))
        best_fitness = np.min(population_fitness)
        numEvalFound = currentEval

        # --- mutation + crossover ---
        for i, xi in enumerate(population):
            index_H = np.random.randint(0, H)
            Fi  = np.random.normal(MemF[index_H], 0.1)
            CRi = np.random.normal(MemCR[index_H], 0.1)
            p   = np.random.rand() * (0.2 - pmin) + pmin

            r1  = random_indexes(1, popsize,     ignore=[i])
            r2  = random_indexes(1, len(memory), ignore=[i, r1])
            xr1 = population[r1]
            xr2 = memory[r2]

            maxbest = max(1, int(p * popsize))
            bests   = np.argsort(population_fitness)[:maxbest]
            xbest   = population[np.random.choice(bests)]

            v = xi + Fi * (xbest - xi) + Fi * (xr1 - xr2)
            v = shade_clip(domain, v, xi)

            idxchange       = np.random.rand(dimension) < CRi
            u[i]            = np.copy(xi)
            u[i, idxchange] = v[idxchange]
            F[i]  = Fi
            CR[i] = CRi

        # --- evaluate each trial individual independently ---
        weights = []
        for i, fitness in enumerate(population_fitness):
            fitness_u = fun(u[i].tolist())

            assert not math.isnan(fitness_u), \
                "NaN fitness for individual {}: {}".format(i, u[i])

            if fitness_u <= fitness:
                if fitness_u < fitness:
                    memory.append(population[i].copy())
                    SF.append(F[i])
                    SCR.append(CR[i])
                    weights.append(fitness - fitness_u)

                if fitness_u < best_fitness:
                    best_fitness = fitness_u
                    numEvalFound = currentEval

                population[i]         = u[i]
                population_fitness[i] = fitness_u

        currentEval += popsize
        memory = limit_memory(memory, memorySize)

        if len(SCR) > 0 and len(SF) > 0:
            Fnew, CRnew = update_FCR(SF, SCR, weights)
            MemF[k]  = Fnew
            MemCR[k] = CRnew
            k = (k + 1) % H
            total_updates += 1

        if observer is not None:
            if total_updates == 0:
                current_mean_f, current_mean_cr = 0.5, 0.5
            elif total_updates < H:
                current_mean_f  = MemF[:total_updates].mean()
                current_mean_cr = MemCR[:total_updates].mean()
            else:
                current_mean_f  = MemF.mean()
                current_mean_cr = MemCR.mean()

            observer(generation, population.copy(), population_fitness.copy(),
                     current_mean_f, current_mean_cr)

    if fid is not None and currentEval >= check_eval:
        bestFitness = np.min(population_fitness)
        fid.write("[%.0e]: %e,%d\n" % (check_eval, abs(bestFitness - fun_best), numEvalFound))
        fid.flush()
        if check_evals:
            check_eval = check_evals.pop(0)

    if fid is not None:
        fid.close()

    bestIndex = np.argmin(population_fitness)
    final_f  = MemF.mean()  if total_updates >= H else (MemF[:total_updates].mean()  if total_updates > 0 else 0.5)
    final_cr = MemCR.mean() if total_updates >= H else (MemCR[:total_updates].mean() if total_updates > 0 else 0.5)
    print("SHADE Mean[F,CR]: ({0:.4f}, {1:.4f})".format(final_f, final_cr))

    return EAresult(fitness=population_fitness[bestIndex], solution=population[bestIndex],
                    evaluations=numEvalFound), bestIndex


def limit_memory(memory, memorySize):
    memory = np.array(memory)
    if len(memory) > memorySize:
        indexes = np.random.permutation(len(memory))[:memorySize]
        memory  = memory[indexes]
    return memory.tolist()


def update_FCR(SF, SCR, improvements):
    total   = np.sum(improvements)
    assert total > 0
    weights = improvements / total
    Fnew  = np.sum(weights * SF * SF) / np.sum(weights * SF)
    Fnew  = np.clip(Fnew,  0, 1)
    CRnew = np.sum(weights * SCR)
    CRnew = np.clip(CRnew, 0, 1)
    return Fnew, CRnew


def shade_clip(domain, solution, original):
    lower, upper = domain
    clip_sol = np.clip(solution, lower, upper)
    if np.all(solution == clip_sol):
        return solution
    idx_low = solution < lower
    idx_up  = solution > upper
    solution[idx_low] = (original[idx_low] + lower) / 2.0
    solution[idx_up]  = (original[idx_up]  + upper) / 2.0
    return solution
