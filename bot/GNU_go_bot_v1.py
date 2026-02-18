import subprocess
import os

# путь к каталогу, где лежит сам скрипт
BOT_DIR = os.path.dirname(os.path.abspath(__file__))
parser= os.path.join(BOT_DIR,"Parser_sfg.py")

# относительный путь к gnugo внутри проекта
GNUGO_PATH = os.path.join(BOT_DIR, "gnugo-3.8", "gnugo.exe")


gtp_process = subprocess.Popen(
    [GNUGO_PATH, "--mode=gtp"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
)

def gtp(cmd: str) -> str:
    gtp_process.stdin.write(cmd + "\n")
    gtp_process.stdin.flush()
    lines = []
    while True:
        line = gtp_process.stdout.readline()
        if not line:
            break  # процесс завершился
        line = line.rstrip("\n")
        if line == "":
            break
        lines.append(line)
    return "\n".join(lines)


sfg_process = subprocess.Popen(
    [GNUGO_PATH, "--mode=gtp"], 
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=0,
)

def sgf(cmd: str) -> str:
    gtp_process.stdin.write(cmd + "\n")
    gtp_process.stdin.flush()
    lines = []
    while True:
        line = gtp_process.stdout.readline()
        if not line:
            break  # процесс завершился
        line = line.rstrip("\n")
        if line == "":
            break
        lines.append(line)
    return "\n".join(lines)

def load_sgf_file(sgf_path: str) -> str:
    
    
    with open(sgf_path, 'r', encoding='utf-8') as f:
        sgf_content = f.read()
    
   
    cmd = f"loadsgf {sgf_content}"
    return sgf(cmd)

#def Get_score(sgf_lines: str) -> tuple[float, float]:

    

"""
def gtp_game():
    print(gtp("boardsize 9"))
    print(gtp("clear_board"))
    print(gtp("showboard"))  # Показать доску
    while True:

        move = gtp("genmove b")[1::]
        
        gtp("play b "+move)

        print(gtp("showboard"))
        print(f"Ход черных: {move}")

        move=input("Ваш ход : ")
        gtp("play w "+move)

        print(f"Ход белых: {move}")
        print(gtp("showboard"))

"""

#
gtp_process.stdin.close()
gtp_process.wait()
