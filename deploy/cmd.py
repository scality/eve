import subprocess
import sys


def cmd(command, ignore_exception=False):
    log = ''
    print('\nCOMMAND : %s' % command)
    process = subprocess.Popen(command, shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)

    # Poll process for new output until finished
    while True:
        nextline = process.stdout.readline()
        if nextline == '' and process.poll() is not None:
            break
        sys.stdout.write(' | ' + nextline)
        sys.stdout.flush()
        log += nextline

    print(u' L________')

    process.communicate()
    exitCode = process.returncode

    if exitCode == 0 or ignore_exception:
        return log
    raise subprocess.CalledProcessError(exitCode, command)
