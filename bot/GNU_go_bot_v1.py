import subprocess
import os

# путь к каталогу, где лежит сам скрипт
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# относительный путь к gnugo внутри проекта
GNUGO_PATH = os.path.join(BASE_DIR, "gnugo-3.8", "gnugo.exe")

print("GNUGO_PATH =", GNUGO_PATH)
print("exists:", os.path.exists(GNUGO_PATH))

proc = subprocess.Popen(
    [GNUGO_PATH, "--mode=gtp"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
)

def gtp(cmd: str) -> str:
    proc.stdin.write(cmd + "\n")
    proc.stdin.flush()
    lines = []
    while True:
        line = proc.stdout.readline()
        if not line:
            break  # процесс завершился
        line = line.rstrip("\n")
        if line == "":
            break
        lines.append(line)
    return "\n".join(lines)


# инициализация доски 9x9 # инициализация-ция-ия-ия
print(gtp("boardsize 9"))
print(gtp("showboard"))
print(gtp("genmove b"))

# СУДА КАМАНДЫ ПИСАТ БУШ


#
proc.stdin.close()
proc.wait()
