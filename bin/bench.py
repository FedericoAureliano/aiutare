#!/usr/bin/env python3
import os
import sys
import subprocess
import signal
import datetime
import concurrent.futures
import json
import importlib
from importlib import util


CONFIG = json.loads(open("./config.json", 'r').read())


def run_problem(program, nickname, command, instance):
    # pass the problem to the command
    invocation = "%s %s" % (command, instance)
    # get start time
    start = datetime.datetime.now().timestamp()
    # run command
    process = subprocess.Popen(
        invocation,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    # wait for it to complete
    try:
        process.wait(timeout=CONFIG["timeout"])
    # if it times out ...
    except subprocess.TimeoutExpired:
        # kill it
        print('TIMED OUT:', repr(invocation), '... killing', process.pid, file=sys.stderr)
        os.killpg(os.getpgid(process.pid), signal.SIGINT)
        # set timeout result
        elapsed = CONFIG["timeout"]
        output = 'timeout (%.1f s)' % CONFIG["timeout"]
    # if it completes in time ...
    else:
        # measure run time
        end = datetime.datetime.now().timestamp()
        elapsed = end - start
        # get result
        stdout = process.stdout.read().decode("utf-8", "ignore")
        stderr = process.stderr.read().decode("utf-8", "ignore")
        output = stdout + stderr
    OUTPUT_HANDLERS[program](nickname, instance, output, elapsed)


# program, specification["id"], specification["command"], problems
def run_solver(args):
    program = args[0]
    nickname = args[1]
    command = args[2]
    instances = args[3]

    for instance in instances:
        run_problem(program, nickname, command, instance)


def signal_handler():
    print("KILLING!")
    try:
        sys.exit(0)
    except SystemExit:
        exit(0)


def import_category():

    global OUTPUT_HANDLERS
    OUTPUT_HANDLERS = {}

    for program in CONFIG["handlers"].items():
        spec = importlib.util.spec_from_file_location("%s_handler" % program[0], program[1])
        new_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(new_module)

        OUTPUT_HANDLERS[program[0]] = new_module.output_handler


def main():
    import_category()

    signal.signal(signal.SIGTERM, signal_handler)

    written_instances = open("./written_instances.json", 'r').read()
    instances = json.loads(written_instances)

    args = [[program, nickname, command, instances] for
            program, specifications in CONFIG["commands"].items() for
            nickname, command in specifications.items()]
    try:
        with concurrent.futures.ProcessPoolExecutor() as executor:
            executor.map(run_solver, args)
    except KeyboardInterrupt:
        print('Interrupted!')
        try:
            sys.exit(0)
        except SystemExit:
            exit(0)


if __name__ == '__main__':
    main()
