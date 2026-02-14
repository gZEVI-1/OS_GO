#!!! Эта хрень не работает, иди в v1 !!!

import subprocess
import sys
import os

# Запуск GnuGo в режиме GTP
proc = subprocess.Popen(
    ['gnugo', '--mode=gtp'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    universal_newlines=True,
    bufsize=0
)

def gtp_command(cmd):
    proc.stdin.write(cmd + '\n')
    proc.stdin.flush()
    response = proc.stdout.readline().strip()
    return response

# Инициализация доски 9x9
print(gtp_command('boardsize 9'))
print(gtp_command('clear_board'))
print(gtp_command('showboard'))  # Показать доску

# Ход ИИ черными
move = gtp_command('genmove b')
print(f"Ход черных: {move}")

# Ваш ход белыми (пример: D4)
print(gtp_command('play w D4'))
print(gtp_command('genmove b'))  # Ответ ИИ

proc.stdin.close()
proc.wait()
