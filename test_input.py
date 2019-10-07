import subprocess

TARGET = ['python3', 'main.py']


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
    assert(out == b'REQUEST RADAR RADAR\n')
    out = child.stdout.readline()
    assert(out == b'WAIT\n')

    child.kill()
