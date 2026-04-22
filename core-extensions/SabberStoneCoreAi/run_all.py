"""
run_all.py  –  Master runner for Hearthstone EA optimization thesis
=======================================================================
PURPOSE
    Compiled to a single Windows EXE via PyInstaller.  At runtime it
    loads each configured .py script from the filesystem (using the
    interpreter that is bundled inside the EXE) and calls its main()
    function the requested number of times.

HOW TO CONFIGURE  (before you compile)
    Edit EXECUTION_PLAN below.  Each entry is:
        ("script_filename.py",  number_of_runs)
    Scripts are executed in order, each run_count times.

HOW TO COMPILE  (run once, on your dev machine)
    See COMPILATION COMMAND at the bottom of this file.
"""

import importlib.util
import sys
import os
import time
import traceback

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURATION  ←  edit this before compiling
# ──────────────────────────────────────────────────────────────────────────────

EXECUTION_PLAN = [
	# ("script_filename.py",  number_of_runs)
	("modified21depth-coevolutionary.py", 10),
	("modified28-coevolutionary.py", 10),
	("modified28normalized-coevolutionary.py", 10),
	("modified63-coevolutionary.py", 10),
	("modified63smooth-coevolutionary.py", 10),
	# ("coevolutionary-working-modified-for-pure-SHADE-5.py",   2),
	# ("coevolutionary-working-modified-for-pure-SHADE-10.py", 2),
	# ("coevolutionary-working-modified-for-pure-SHADE-15.py",   2),
	# ("coevolutionary-working-modified-for-SHADE-like-5.py",   2),
	# ("coevolutionary-working-modified-for-SHADE-like-10.py", 2),
	# ("coevolutionary-working-modified-for-SHADE-like-15.py",   2),
]


# ──────────────────────────────────────────────────────────────────────────────
# END OF CONFIGURATION  –  do not edit below unless you know what you're doing
# ──────────────────────────────────────────────────────────────────────────────


def get_base_dir() -> str:
	"""
	Returns the directory that contains run_all.exe (frozen) or run_all.py
	(dev mode).  All individual .py scripts must live in this same folder.
	"""
	if getattr(sys, "frozen", False):
		# Running as a compiled PyInstaller EXE
		return os.path.dirname(sys.executable)
	else:
		# Running as a plain .py script during development
		return os.path.dirname(os.path.abspath(__file__))


def setup_log_file(base_dir: str):
	"""
	Opens a top-level run_all log file so your tutor can see what happened
	even after the console window closes.
	"""
	log_path = os.path.join(
		base_dir,
		f"run_all-log-{time.strftime('%m%d%Y-%H%M%S')}.txt"
	)
	log_file = open(log_path, "w", encoding="utf-8")
	return log_file


def tee(log_file, *args, **kwargs):
	"""Print to both stdout and the log file simultaneously."""
	line = " ".join(str(a) for a in args)
	print(line, **kwargs)
	log_file.write(line + "\n")
	log_file.flush()


def load_script_module(script_path: str):
	"""
	Dynamically loads a .py file and returns it as a module object.
	The __name__ of the loaded module is deliberately NOT '__main__',
	so every script's  `if __name__ == '__main__':` guard is respected
	and auto-execution is suppressed.
	"""
	script_dir = os.path.dirname(os.path.abspath(script_path))
	if script_dir not in sys.path:
		sys.path.insert(0, script_dir)

	module_name = (
		os.path.basename(script_path)
		.replace(".py", "")
		.replace("-", "_")  # hyphens are invalid in Python identifiers
	)
	spec = importlib.util.spec_from_file_location(module_name, script_path)
	if spec is None:
		raise ImportError(f"Cannot create module spec for: {script_path}")
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


def run_plan(log):
	base_dir = get_base_dir()
	tee(log, "=" * 70)
	tee(log, f"  run_all.py  –  started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
	tee(log, f"  Base directory : {base_dir}")
	tee(log, "=" * 70)

	total_scripts = sum(count for _, count in EXECUTION_PLAN)
	completed = 0
	wall_start = time.time()

	for script_name, run_count in EXECUTION_PLAN:
		script_path = os.path.join(base_dir, script_name)

		# ── sanity check ──────────────────────────────────────────────────
		if not os.path.isfile(script_path):
			tee(log, f"\n[ERROR] Script not found, skipping: {script_path}")
			tee(log, "        Make sure the .py file is in the same folder as run_all.exe")
			continue

		# ── load the module once; reuse across runs ───────────────────────
		tee(log, f"\n{'─' * 70}")
		tee(log, f"  Loading module : {script_name}")
		try:
			module = load_script_module(script_path)
		except Exception:
			tee(log, f"[ERROR] Failed to load {script_name}:")
			tee(log, traceback.format_exc())
			continue

		if not hasattr(module, "main"):
			tee(log, f"[ERROR] {script_name} has no main() function – skipping.")
			continue

		# ── execute run_count times ───────────────────────────────────────
		for run_idx in range(1, run_count + 1):
			completed += 1
			tee(log,
				f"\n  ► [{completed}/{total_scripts}]  "
				f"{script_name}  –  run {run_idx}/{run_count}  "
				f"(wall time so far: {time.time() - wall_start:.0f}s)")
			run_start = time.time()
			try:
				module.main(display=False)
			except Exception:
				tee(log, f"[ERROR] Exception during {script_name} run {run_idx}:")
				tee(log, traceback.format_exc())
				tee(log, "  → Continuing with next run...")
			else:
				tee(log,
					f"  ✓ Finished in {time.time() - run_start:.1f}s")

	tee(log, "\n" + "=" * 70)
	tee(log, f"  All done.  Total wall time: {time.time() - wall_start:.1f}s")
	tee(log, "=" * 70)


def main():
	if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
		if sys._MEIPASS not in sys.path:
			sys.path.insert(0, sys._MEIPASS)

	base_dir = get_base_dir()
	log = setup_log_file(base_dir)
	try:
		run_plan(log)
	finally:
		log.close()
	input("\nPress ENTER to close this window...")


if __name__ == "__main__":
	main()

# ══════════════════════════════════════════════════════════════════════════════
# COMPILATION COMMAND
# ══════════════════════════════════════════════════════════════════════════════
#
# Run this ONCE on your development machine (with Python + PyInstaller installed):
#
#   pip install pyinstaller inspyred numpy
#
#   pyinstaller ^
#       --onefile ^
#       --console ^
#       --name run_all ^
#       --hidden-import=inspyred ^
#       --hidden-import=inspyred.ec ^
#       --hidden-import=inspyred.ec.analysis ^
#       --hidden-import=inspyred.ec.observers ^
#       --hidden-import=inspyred.ec.terminators ^
#       --hidden-import=numpy ^
#       --hidden-import=numpy.random ^
#       run_all.py
#
# The output EXE will be at:  dist\run_all.exe
#
# ──────────────────────────────────────────────────────────────────────────────
# WHAT GOES IN THE ZIP (directory structure your tutor unpacks)
# ──────────────────────────────────────────────────────────────────────────────
#
#   master_folder\
#   ├── run_all.exe                          ← the only thing to double-click
#   ├── modified21depth-coevolutionary.py    ← must be here (same folder as exe)
#   ├── modified28-coevolutionary.py
#   ├── modified28normalized-coevolutionary.py
#   ├── modified63-coevolutionary.py
#   ├── modified63smooth-coevolutionary.py
#   ├── MODIFIED21DEPTH_PARALLEL_HS\         ← C# simulator folders
#   ├── MODIFIED28_PARALLEL_HS\
#   ├── MODIFIED28NORMALIZED_PARALLEL_HS\
#   ├── MODIFIED63_PARALLEL_HS\
#   └── MODIFIED63SMOOTH_PARALLEL_HS\
#
# Logs are written to this same folder automatically.
# ══════════════════════════════════════════════════════════════════════════════
