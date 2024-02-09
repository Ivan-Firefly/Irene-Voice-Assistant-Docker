import requests
import json
import os
import random

from vacore import VACore

modname = os.path.basename(__file__)[:-3]  # calculating modname


# функция на старте
def start(core: VACore):
    manifest = {
        "name": "Триггер автоматизаций Home Assistant",
        "version": "1.0",
        "default_options": {
            "hassio_url": "http://hassio.lan:8123/",
            "hassio_key": "",  # получить в /profile, "Долгосрочные токены доступа"
            "default_reply": ["Сделано", "Готово", "Выполнено"],
            # ответить если в описании скрипта не указан ответ в формате "ttsreply(текст)"
        },

        "commands": {
            "давай": HA_event_trigger,
        }
    }

    return manifest


def start_with_options(core: VACore, manifest: dict):
    headers = {
        "Authorization": f"Bearer " + manifest["options"]["hassio_key"],
        "content-type": "application/json",
    }

    events = requests.get(manifest["options"]["hassio_url"] + 'api/events', headers=headers).json()

    trigger_events = []
    for event in events:
        if event['event'].startswith('!'):
            event_text = event['event'][1:].split()[0]
            trigger_events.append(event_text)
    trigger_events = '|'.join(trigger_events)

    events_dict = {}
    events_dict[trigger_events] = ""
    merged_keys = '|'.join(list(manifest["commands"].keys()) + list(events_dict.keys()))
    merged_commands = '|'.join([*manifest['commands'], *events_dict.keys()])
    manifest['commands'] = {merged_commands: manifest['commands'].popitem()[1]}

    return manifest


def HA_event_trigger(core: VACore, phrase: str):
    options = core.plugin_options(modname)
    plugin_commands = core.plugin_manifest(modname)['commands']

    if options["hassio_url"] == "" or options["hassio_key"] == "":
        print(options)
        core.play_voice_assistant_speech("Нужен ключ или ссылка для Хоум Ассистента")
        return

    try:
        headers = {
            "Authorization": f"Bearer " + options["hassio_key"],
            "content-type": "application/json",
        }
        events = requests.get(options["hassio_url"] + 'api/events', headers=headers).json()
        matched_event = True
        for event in events:
            event_obj=event["event"].split(' ', 1)[1] if ' ' in event["event"] else event["event"]
            if phrase == event_obj or phrase in event["event"]:
                requests.post(options["hassio_url"] + 'api/events/' + event["event"], headers=headers)
                try:
                    reply = event["event"].split("=", 1)[1]
                except:
                    reply = options["default_reply"][random.randint(0, len(options["default_reply"]) - 1)]

                core.play_voice_assistant_speech(reply)
                print(reply)
                matched_event = False
                break
        if matched_event:
            core.play_voice_assistant_speech("Не могу найти нужную автоматизацию")
            print('Не могу найти нужную автоматизацию')

    except:
        import traceback
        traceback.print_exc()
        reply = "Не получилось выполнить скрипт"
        core.play_voice_assistant_speech(reply)
        print(reply)
        return
