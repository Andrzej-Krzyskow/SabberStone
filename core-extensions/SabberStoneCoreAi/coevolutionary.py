import signal
from random import Random
from random import randint

import inspyred
import time
import os
import subprocess, threading
import sys

#from inspyred.ec import Individual

DEBUG = True
DECKS = ["RenoKazakusMage", "MidrangeJadeShaman" , "AggroPirateWarrior"]
HERO_BY_DECK = {"RenoKazakusMage":"MAGE", "MidrangeJadeShaman":"SHAMAN" , "AggroPirateWarrior":"WARRIOR"}
NUM_GAMES = 20
NUM_WEIGHTS = 21 #21
TEMP_FILE_NAME = "results.tmp"
POP_SIZE = 10
NUM_THREADS = 8
MAX_EVALUATIONS = 1000
TEST_DUMMY = True #Esto evita lanzar el comando, solo usar para depurar


lock = threading.Lock()

victories = [] #GLOBAL VARIABLE TO UPDATE RESULTS
victories_versus = []

class Command(object):
	def __init__(self, cmd):
		self.cmd = cmd
		self.process = None

	def run(self, timeout):
		def target():
			#print 'Thread started'
			self.process = subprocess.Popen(self.cmd, shell=True,  preexec_fn=os.setsid)
			self.process.communicate()
			#print 'Thread finished'

		thread = threading.Thread(target=target)
		thread.start()

		thread.join(timeout)
		#print "EXIT WITH CODE "+str(self.process.returncode)
		if thread.is_alive():
			print('Terminating process')

			#self.process.terminate()
			os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
			thread.join()
			print("Game lasted a lot :/")
			return False
		return True


def chunks(l, n):
	"""Yield successive n-sized chunks from l."""
	for i in range(0, len(l), n):
		yield l[i:i + n]


def print_squared_array(the_array):
	l = ""
	for i in range(0,len(the_array)):
		total = 0
		for j in range(0,len(the_array)): #WARNING, THE ARRAY IS SQUARED!
			if isinstance(the_array[i][j],float):
				v="{0:.2f}".format(the_array[i][j])
			else:
				v=str(the_array[i][j])
			l = l+v+" "
			total += the_array[i][j]
		l = l+" TOTAL: "+str(total)+"\n"
	return l


def my_file_observer(population, num_generations, num_evaluations, args):

	try:
		statistics_file = args['statistics_file']
	except KeyError:
		statistics_file = open('inspyred-statistics-file-{0}.csv'.format(time.strftime('%m%d%Y-%H%M%S')), 'w')
		args['statistics_file'] = statistics_file
		args['init_time'] = time.time()
	try:
		individuals_file = args['individuals_file']
	except KeyError:
		individuals_file = open('inspyred-individuals-file-{0}.csv'.format(time.strftime('%m%d%Y-%H%M%S')), 'w')
		args['individuals_file'] = individuals_file
	try:
		matrix_file = args['matrix_file']
	except KeyError:
		matrix_file = open('inspyred-matrix-file-{0}.csv'.format(time.strftime('%m%d%Y-%H%M%S')), 'w')
		args['matrix_file'] = matrix_file

	stats = inspyred.ec.analysis.fitness_statistics(population)
	worst_fit = stats['worst']
	best_fit = stats['best']
	avg_fit = stats['mean']
	med_fit = stats['median']
	std_fit = stats['std']
	diff_time = time.time()-args['init_time']

	statistics_file.write(
		'{0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}\n'.format(num_generations, len(population), worst_fit, best_fit, med_fit,
													 avg_fit, std_fit, diff_time))


	for i, p in enumerate(population):
		indi = repr(p.candidate[:len(p.candidate)//2])
		dict_battles = args["_dictionary_battles"][indi]
		battles = ""
		for v in dict_battles.keys():
			if v != "TOTAL":
				battles += str(dict_battles[v])+"-"

		individuals_file.write('{0}, {1}, {2}, {3}, BATTLES: {4}\n'.format(num_generations, i, p.fitness, str(p.candidate),battles))

	matrix_file.write(str(num_generations))
	matrix_file.write("\nVICTORIES\n")
	matrix_file.write(args["_matrix_victories"])
	matrix_file.write("\nTURNS_WIN\n")
	matrix_file.write(args["_matrix_turns_win"])
	matrix_file.write("\nTURNS_LOSE\n")
	matrix_file.write(args["_matrix_turns_lose"])
	matrix_file.write("\nHEALTH_WIN\n")
	matrix_file.write(args["_matrix_health_win"])
	matrix_file.write("\nHEALTH_LOSE\n")
	matrix_file.write(args["_matrix_health_lose"])


	statistics_file.flush()
	individuals_file.flush()
	matrix_file.flush()


def generate_weights(random, args):
	size = args.get('num_weights')
	return [random.uniform(0, 1) for i in range(size)]


def individual_to_commandline(ind):
	#if ind is Individual get only the num_weights! else check that ind is a list of num_weights
	param = ""
	for e in ind:
		param = param+str(e)+"#"
	param = param[:-1]
	return param


def parse_file(file_name):
	print("PARSING FILE "+file_name)
	with open(file_name, "r") as fp : lines = fp.readlines()
	#print("FILE IS "+str(lines))
	match_info = filter(None, lines[-1].split(" "))
	return int(match_info[0]),int(match_info[1]),int(match_info[3]),int(match_info[4]),int(match_info[5]),int(match_info[6])


def launch_simulator(f1, f2, d1, d2, thread_id,temp_file_name):

	test = TEST_DUMMY
	file_name = thread_id+temp_file_name



	os.system("rm "+file_name)
	cml1 = individual_to_commandline(f1)
	cml2 = individual_to_commandline(f2)
	if test:
		w = randint(0,NUM_GAMES)
		w1 = w
		w2 = NUM_GAMES - w
		tw = randint(0,15*NUM_GAMES)
		tl = randint(0,15*NUM_GAMES)
		hw = randint(0,5*NUM_GAMES)
		hl = randint(0,5*NUM_GAMES)
		time.sleep(randint(0,0))
		command_line = "echo {0} {1} {2} {3} {4} {5} {6} > {7} ".format(w1,w2,NUM_GAMES,tw,tl,hw,hl,file_name)
		print("echo ESTO NO SE EJECUTA dotnet run --project /home/pgarcia/code/PARALLEL_HS/SabberStone"+thread_id+"/core-extensions/SabberStoneCoreAi/SabberStoneCoreAi.csproj")
		print("echo {0} {1} {2} {3} {4} {5} {6} {7}".format(d1,HERO_BY_DECK[d1],cml1,d2,HERO_BY_DECK[d2],cml2,NUM_GAMES," > "+file_name))
	else:
		command_line = "dotnet run --project /home/pgarcia/code/PARALLEL_HS/SabberStone"+thread_id+"/core-extensions/SabberStoneCoreAi/SabberStoneCoreAi.csproj"
		command_line += " {0} {1} {2} {3} {4} {5} {6} {7}".format(d1,HERO_BY_DECK[d1],cml1,d2,HERO_BY_DECK[d2],cml2,NUM_GAMES," > "+file_name)

	if DEBUG:print("\t\t"+command_line)
	com = Command(command_line)

	attempts = 0
	finished = False
	while not finished:
		print("Launching attempt " + str(attempts))
		finished = com.run(500)  # 1200
		attempts = attempts + 1
		if attempts == 3:
			finished = True


	w1,w2, tw, tl, hw, hl = parse_file(file_name)
	if DEBUG:print ("\t\tNUMBERS ARE "+str(w1)+" "+str(w2))
	return w1, w2, tw, tl, hw, hl

def execute_simulator_in_thread(battle):
	thread_name = threading.currentThread().getName()
	print(thread_name+" STARTING ")
	global victories
	id_1 = battle[0]
	id_2 = battle[1]
	weights_1 = battle[2]
	weights_2 = battle[3]
	deck_1 = battle[4]
	deck_2 = battle[5]

	v1, v2, tw, tl, hw, hl = launch_simulator(weights_1,weights_2,deck_1,deck_2,thread_name,TEMP_FILE_NAME)
	with lock:
		victories[id_1]["TOTAL"] += v1
		victories[id_1][deck_1 + deck_2] += v1
		victories[id_2]["TOTAL"] += v2
		victories[id_2][deck_2 + deck_1] += v2
		victories_versus[id_1][id_2] +=v1
		victories_versus[id_2][id_1] +=v2
		turns_win[id_1][id_2] += tw
		turns_win[id_2][id_1] += tl
		turns_lose[id_1][id_2] += tl
		turns_lose[id_2][id_1] += tw
		health_win[id_1][id_2] += hw
		health_win[id_2][id_1] += hl
		health_lose[id_1][id_2] += hl
		health_lose[id_2][id_1] += hw
	print(thread_name+" FINISHING")

def evaluate_hearthstone(candidates, args):
	args["_dictionary_battles"] ={}

	parents = args['_ec'].population

	to_fight = []
	for p in parents:
		n = len(p.candidate) // 2 #removing the half (taus)
		to_fight.append(p.candidate[:n])

	num_parents = len(parents)

	to_fight = to_fight + candidates

	global victories
	global victories_versus
	global turns_win
	global turns_lose
	global health_win
	global health_lose

	victories = []
	victories_versus = []
	turns_win = []
	turns_lose = []
	health_win = []
	health_lose = []

	fitness = []

	for i in range(0,len(to_fight)):
		victories.append({})
		victories_versus.append([])
		turns_win.append([])
		turns_lose.append([])
		health_win.append([])
		health_lose.append([])
		victories[i]["TOTAL"] = 0
		for d1 in DECKS:
			for d2 in DECKS:
				victories[i][d1+d2] = 0
		for j in range(0,len(to_fight)):
			victories_versus[i].append([])
			turns_win[i].append([])
			turns_lose[i].append([])
			health_win[i].append([])
			health_lose[i].append([])
			victories_versus[i][j] = 0
			turns_win[i][j] = 0
			turns_lose[i][j] = 0
			health_win[i][j] = 0
			health_lose[i][j] = 0

	battles_list = []
	for i,f1 in enumerate(to_fight):
		if DEBUG: print ("INDIVIDUAL "+str(f1))
		for j,f2 in enumerate(to_fight):
			for d1 in DECKS:
				for d2 in DECKS:
					if i<j: #NOT COMPARING WITH HIMSELF!
						#if DEBUG: print "\tVERSUS " + str(f2)
						#if DEBUG: print ("\t\tCONFRONTING {0} vs {1} Ind{2} vs Ind{3}".format(d1,d2,f1,f2))
						battles_list.append([i,j,f1,f2,d1,d2])

	chunk_battles = chunks(battles_list,NUM_THREADS)

	for parallel_battle in chunk_battles:
		threads = []
		if DEBUG: print("EXECUTING PARALLEL BATTLES: "+str(len(parallel_battle)))
		for i,battle in enumerate(parallel_battle):
			t = threading.Thread(target=execute_simulator_in_thread, args=(battle,), name=str(i))
			threads.append(t)
		for t in threads:
			t.start()
		for t in threads:
			t.join()
		#print("PRESS ANY KEY TO CONTINUE")
		#sys.stdin.read(1)

	#for battle in battles_list:
		#print(battle)
		#execute_simulator_in_thread(battle,TEMP_FILE_NAME)

	for i,v in enumerate(victories):
		args["_dictionary_battles"].update({repr(to_fight[i]): victories[i]})
		if i<num_parents:
			#Updating parent fitness
			args["_ec"].population[i].fitness = victories[i]["TOTAL"]
		else:
			fitness.append(victories[i]["TOTAL"])

	print("VICTORIES")
	args["_matrix_victories"]  = print_squared_array(victories_versus)

	for i in range(0,len(victories_versus)):
		for j in range(0,len(victories_versus)): #WARNING, THE ARRAY IS SQUARED!
			if i !=j:
				ij = float(victories_versus[i][j])
				ji = float(victories_versus[j][i])
				if ij > 0: #To avoid divide by 0
					turns_win[i][j] = turns_win[i][j]/ij
					health_win[i][j] = health_win[i][j] / ij
				if ji > 0:
					turns_lose[i][j] = turns_lose[i][j] / ji
					health_lose[i][j] = health_lose[i][j] / ji

	print("TURNS TO WIN")
	args["_matrix_turns_win"] = print_squared_array(turns_win)
	print("TURNS TO LOSE")
	args["_matrix_turns_lose"] = print_squared_array(turns_lose)
	print("HEALTH TO WIN")
	args["_matrix_health_win"] = print_squared_array(health_win)
	print("HEALTH TO LOSE")
	args["_matrix_health_lose"] =print_squared_array(health_lose)

	return fitness


def run_one(prng=None, display=False):
	if prng is None:
		prng = Random()
		prng.seed(time.time())

	time1 = time.time()
	ea = inspyred.ec.ES(prng)
	ea.terminator = [inspyred.ec.terminators.evaluation_termination] #inspyred.ec.terminators.diversity_termination

	ea.observer = [inspyred.ec.observers.stats_observer, my_file_observer]
	final_pop = ea.evolve(generator=generate_weights,
						  num_weights = NUM_WEIGHTS,
						  evaluator=evaluate_hearthstone,
						  pop_size=POP_SIZE,
						  bounder=inspyred.ec.Bounder(0,1),
						  maximize=True,
						  max_evaluations=MAX_EVALUATIONS)

	if display:
		best = max(final_pop)
		print('Best Solution: \n{0}'.format(str(best)))
	time2 = time.time()
	print('TIME ELAPSED = '+str(time2 - time1))
	return ea

def main(prng=None, display=False):
	for i in range(0,10):
		run_one(prng,display)


if __name__ == '__main__':
	main(display=True)
