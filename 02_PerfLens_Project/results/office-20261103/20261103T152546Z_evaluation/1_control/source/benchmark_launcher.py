"""Wait for parent job assignment before allowing an external command to execute."""
import subprocess
import sys

if __name__=='__main__':
    if sys.stdin.readline() != 'run\n':
        raise SystemExit('Benchmark launch was not authorized by its runner')
    raise SystemExit(subprocess.call(sys.argv[1:],stdin=subprocess.DEVNULL))
