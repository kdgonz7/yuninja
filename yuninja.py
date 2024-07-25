import colorama
import os
import subprocess
import sys

from sys import exit
from pathlib import Path
from time import time
from threading import Thread
from shutil import copyfile
from os import makedirs
from io import StringIO

# settings
jobs = 0
quiet = False
srcdir = "src"
buildmode = False

n = 0

def print_usage():
	print("""Usage: build.py [-jobs <N>] [-quiet] [-help]
	This program builds all yuescript files in a `src' directory, and outputs them to the root directory. Primarily
	Designed for Garry's Mod addons. But can be configured to run in any environment.

	-jobs <N>		- number of threads to use (more jobs, more parallel)
	-quiet			- don't print anything to STDOUT
	-srcdir	<D>		- what directory should be used for source files? defaults to `src'
	-help			- this help
	
Commands:
	build			- build all yuescript files in the 
	""")

while n < len(sys.argv):
	if sys.argv[n] == "-jobs" or sys.argv[n] == "-j":
		n += 1									# -jobs <N>
		if n >= len(sys.argv):
			print("error: -jobs requires an argument <N>")
			exit(1)
		jobs = int(sys.argv[n])	#				<N>
		n += 1									#				 N <...>
		continue
	if sys.argv[n] == "-help" or sys.argv[n] == "-h":
		print_usage()
		exit(0)
	if sys.argv[n] == "-quiet" or sys.argv[n] == "-q" or sys.argv[n] == "--":
		quiet = True

	if sys.argv[n] == "-srcdir":
		n += 1
		if n >= len(sys.argv):
			print("error: -srcdir requires an argument <DIR>")
			exit(1)
		srcdir = sys.argv[n]
		n += 1
		continue

	if sys.argv[n] == "build":
		buildmode = True
	n += 1

if not buildmode: print_usage(); exit(0)

msg = lambda x: print(colorama.Fore.MAGENTA + colorama.Style.DIM + "[yuninja]" + colorama.Style.RESET_ALL + " " + x) and sys.stdout.flush()
if quiet:
	msg = lambda x: sys.stdout.flush()

msg("checking for yue files in the source directory with " + str(jobs) + " worker jobs")

now = time()

tocompile = []

for dirpath, dirnames, filenames in os.walk(srcdir):
	if not Path(dirpath[4:]).is_dir():
		if not quiet:
			msg(f"could not find `{dirpath[4:]}`, create it")
		os.mkdir(dirpath[4:])
	for f in filenames:
		if f.endswith(".yue"):
			if not quiet:
				msg(f"compiling {f}...")

			tocompile.append(os.path.join(dirpath, f))

def subcomp(f, dirpath):
	rc = subprocess.run(["yue", f"{f}", "-o", f"{f[4:-4]}.lua"], stderr=subprocess.DEVNULL)

	if rc.returncode != 0:
		msg("error when compiling. see output above.")
		exit(1)

	filename = f[4:-4]
	if Path(".cache").is_dir():
		makedirs(f".cache/{os.path.dirname(filename)}", exist_ok=True)
		if Path(".cache/" + filename + ".lua").is_file():
			g = open(f".cache/{filename}.lua", "r")
			r = open(f"{filename}.lua", "r")

			if g.read() == r.read():
				msg(f"{f} is up to date")

			g.close()
			r.close()

	if not Path(".cache").is_dir():
		os.mkdir(".cache")

	cache_filename = f".cache/{filename}.lua"
	copyfile(f"{f[4:-4]}.lua", cache_filename)
	
threads = []

if len(tocompile) == 0:
	msg("nothing to do")
	exit(0)

if jobs > 0:
	i = 0
	while i < len(tocompile):
		if jobs > 0:
			for j in range(jobs):
				if i >= len(tocompile):
					break

				t = Thread(target=subcomp, args=(tocompile[i], dirpath))
				t.start()

				threads.append(t)
				i += 1

			for t in threads:
				t.join()
else:
	for f in tocompile:
		subcomp(f, dirpath)

time_taken = time() - now

msg(f"build finished ({time_taken:.4f}s)")