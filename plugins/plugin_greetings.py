# Приветствие (и демо-плагин)
# author: Vladislav Janvarev (inspired by EnjiRouz)

import random
from vacore import VACore

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "Привет",
        "version": "1.0",
        "require_online": False,

        "commands": {
            "привет|доброе утро": play_greetings,
        }
    }
    return manifest

def play_greetings(core:VACore, phrase: str):
    """
    Проигрывание случайной приветственной речи
    """
    greetings = [
        "И тебе привет!",
        "Рада тебя видеть!",
    ]

    core.play_voice_assistant_speech(greetings[random.randint(0, len(greetings) - 1)])
