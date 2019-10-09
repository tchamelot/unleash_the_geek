import subprocess
import os

TOPDIR = os.path.dirname(os.path.abspath(__file__))
TARGET = ['python3', TOPDIR + '/main.py']


def test_first_round():
    child = subprocess.Popen(TARGET,
                             stdout=subprocess.PIPE,
                             stdin=subprocess.PIPE)

    input = b"""\
10 5
0 0
? 0 ? 0 ? 0 ? 0 ? 0 ? 0 ? 0 ? 0 ? 0 ? 0
? 0 ? 0 ? 0 ? 0 ? 0 ? 0 ? 0 ? 0 ? 0 ? 0
? 0 ? 0 ? 0 ? 0 ? 0 ? 0 ? 0 ? 0 ? 0 ? 0
? 0 ? 0 ? 0 ? 0 ? 0 ? 0 ? 0 ? 0 ? 0 ? 0
? 0 ? 0 ? 0 ? 0 ? 0 ? 0 ? 0 ? 0 ? 0 ? 0
4 0 0
0 0 0 1 -1
1 0 0 2 -1
2 1 0 3 -1
3 1 0 4 -1
"""
    child.stdin.write(input)
    child.stdin.flush()
    out = child.stdout.readline()
    print(out)
    assert(out == b'REQUEST RADAR REQ_RADAR_5_8\n')
    out = child.stdout.readline()
    print(out)
    # assert(out == b'REQUEST TRAP REQ_TRAP_0_0\n')

    child.kill()
