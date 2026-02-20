import os
import bot.GNU_go_bot_v1 as gnu

scripts_dir = os.path.dirname(os.path.abspath(__file__))
print("base_dir =", scripts_dir)
project_dir = os.path.split(scripts_dir)[0]
print ('project_dir =', project_dir)
bot_dir = os.path.join(project_dir, "bot")
print("bot_dir =", bot_dir)
bot= os.path.join(bot_dir, "GNU_go_bot_v1.py")
print("bot =", bot)


