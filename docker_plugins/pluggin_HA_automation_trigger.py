import requests
import json

from vacore import VACore

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "Триггер скриптов Home Assistant",
        "version": "1.0",
        "default_options": {
            "hassio_url": "http://hassio.lan:8123/",
            "hassio_key": "", # получить в /profile, "Долгосрочные токены доступа"
            "default_reply": [ "Сделано", "Готово", "Выполнено" ], # ответить если в описании скрипта не указан ответ в формате "ttsreply(текст)"
        },

        "commands": {
            "хочу|сделай|я буду": hassio_run_script,
        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass


def main(core:VACore, phrase:str):
    options = core.plugin_options(modname)

    if options["hassio_url"] == "" or options["hassio_key"] == "":
        print(options)
        core.play_voice_assistant_speech("Нужен ключ или ссылка для Хоум Ассистента")
        return
    try:
        headers = {
            "Authorization": f"Bearer " + options["hassio_key"],
            "content-type": "application/json",
        }
        phrase='call'
        events = requests.get(options["hassio_url"]+'api/events', headers=headers).json()
        matched_webhook = True
        for event in events:
            if event["event"] == phrase:
                requests.post(options["hassio_url"]+'api/events'+ event["event"], headers=headers)
                script_desc = str(
                    hassio_scripts[event]["description"])  # бонус: ищем что ответить пользователю из описания скрипта
                if "ttsreply(" in script_desc and ")" in script_desc.split("ttsreply(")[1]:  # обходимся без re :^)
                    core.play_voice_assistant_speech(script_desc.split("ttsreply(")[1].split(")")[0])
                else:  # если в описании ответа нет, выбираем случайный ответ по умолчанию
                    core.play_voice_assistant_speech(
                        options["default_reply"][random.randint(0, len(options["default_reply"]) - 1)])
                matched_webhook = False
                break
        if matched_webhook:
            core.play_voice_assistant_speech("Не могу найти нужную автоматизацию")
            print('Не могу найти нужную автоматизацию')

    except:
        import traceback
        traceback.print_exc()
        core.play_voice_assistant_speech("Не получилось выполнить скрипт")
        return
