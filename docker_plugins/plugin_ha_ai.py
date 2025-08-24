import fnmatch
import json
import os
import random
import requests

from vacore import VACore



modname = os.path.basename(__file__)[:-3]  # calculating modname


# функция на старте
def start(core: VACore):
    manifest = {
        "name": "ИИ управление Home Assistant",
        "version": "1.0",
        'require_online': True,
        "default_options": {
            "api_key":"",
            "AI_model":"",
            "base_url":"", # для google - https://generativelanguage.googleapis.com/v1beta/models/, для vsegpt - https://api.vsegpt.ru/v1, так же можно использовать и локальные LLM.
            "hassio_url": "http://ip:8123/",
            "hassio_key": "",  # получить в /profile, "Долгосрочные токены доступа"
            "default_reply": ["Сделано", "Готово", "Выполнено"],
            "entity_id_blacklist" : "camera.xiaomi_cloud_map_extractor, update.*, sensor.sun*, *dafang*",  # сюда через запятую можно указывать устройства из ХА которые не будут отправлятся в ИИ (вам есть что скрывать, либо устройство генерирует кучу бесполезных состояний).
            "entity_id_whitelist" : "", # если есть хоть один символ/устройство в этом листе, у него появлятся приоритет над black list и соостветсвенно в ИИ уйдут только те устройства, что перечислены в белом листе (самый эффективный способ уменьшения кол-ва токенов).
            "item_blacklist":"last_changed, last_reported, last_updated, context", # нектороые устройство в ХА черезчур "богаты" на параметры и атрибуты. Опять же для сокращения кол-ва токенов можно из каждого устройства убрать типовые лишние параметры (когда было включено, когда последний раз было опрос и т.д.).
            "prompt":"You are an expert in Home Assistant REST API. Your main aim is to convert user input written in natural language to Home Assistant REST API command."  #это "системные правила" для ИИ. Его можно (и нужно) настривать под себя, чтоб добится наилучшего "понимания" контекста. Способ выдачи ответа (функция) описан внутри кода в переменной TextToHomeAssistantAPI (в настройки не вынесена), она же которая передается в tools.
                            "If user ask you something about music, volume, tracks, albums, use media_player entities."
                            "If user ask you to change volume in percentages, convert it to decimal an use only 1 digit after dot."
                            "If user ask you to change brightness in percentages, use value as whole number, not as percentage."
                            "If user ask you to increase or decrease volume read the current state value of the entity and add or subtract 0.2 from current sate value."
                            "If user ask you to increase or decrease brightness read the current state value of the entity and add or subtract 50 from current sate value."
                            "First step: you need to define which entity user calls in his phrase."
                            "Second step: find subject entity in the given Home Assistant structure. Don't make up non-existing entities, actions, or parameters; use only entities from the user input.If you can't find existing entity in provided by user Home Assistant structure, put 404."
                            "Third step: define which services are available for subject entity."
                            "Fourth step: find which of the subject services suits best to the user action request from the phrase. Don't make up non-existing entities, actions, or parameters; use only entities from the user input. If you can't find existing service in provided by user Home Assistant structure, put 404."
                            "Optional step: if user asks you to show or tell something like temperature, time, or state of an entity, use the current state of the entity and put its value with a # marker."

        },


        "commands": {
            "дом-дурачок": HA_AI,
        }
    }

    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass

def matches_pattern(value, patterns):
    if not value:
        return False
    return any(fnmatch.fnmatch(value, pattern) for pattern in patterns)

def sanitize_tokens(attributes):
    if isinstance(attributes, dict):
        new_attrs = {}
        for k, v in attributes.items():
            if "token" in k.lower() or "icon" in k.lower():
                continue
            elif isinstance(v, dict):
                new_attrs[k] = sanitize_tokens(v)
            else:
                new_attrs[k] = v
        return new_attrs
    return attributes

def clean_json(data, entity_id_blacklist, entity_id_whitelist,item_blacklist):
    entity_id_blacklist = format_dict(entity_id_blacklist)
    entity_id_whitelist = format_dict(entity_id_whitelist)
    item_blacklist = format_dict(item_blacklist)



    filtered_data = []

    for item in data:
        domain = item.get("domain", "")
        entity_id = item.get("entity_id", "")


        if entity_id_whitelist:
            if not matches_pattern(entity_id, entity_id_whitelist):
                continue
        else:
            if matches_pattern(entity_id, entity_id_blacklist):
                continue


        clean_item = item.copy()
        clean_item["attributes"] = sanitize_tokens(item.get("attributes", {}))


        for key in item_blacklist:
            clean_item.pop(key, None)

        filtered_data.append(clean_item)

    return filtered_data

def format_dict(input_data):
    if isinstance(input_data, str):
        items = input_data.split(',')
        return set(item.strip() for item in items if item.strip())
    elif isinstance(input_data, (set, list)):
        return set(item.strip() for item in input_data if item.strip())

def get_ha_data(base_url, token):

    url = f"{base_url}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    response = requests.get(url, headers=headers, timeout=10)
    return response.json()

def ha_vsegpt_ai(options, function, generation_params, user_input):
    url = f"{options['base_url'].rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {options['api_key']}",
        "Content-Type": "application/json",
    }

    payload = {
        "messages": [
            {"role": "system", "content": options["prompt"]},
            {"role": "user", "content": user_input}
        ],
        "tools": [
            {
                "type": "function",
                "function": function
            }
        ],
        **generation_params
    }

    response = requests.post(url, headers=headers, json=payload)
    response=response.json()
    print(response)
    reply = None

    if "choices" in response and response["choices"]:
        choice = response["choices"][0]

        # check if tool calls are present
        message = choice.get("message", {})
        tool_calls = message.get("tool_calls", [])

        for call in tool_calls:
            args = call["function"]["arguments"]

            if isinstance(args, str):
                args = json.loads(args)

            try:
                api_ha_url = args["api_ha_url"]
                api_ha_data = json.loads(args["api_ha_data"].replace("'", '"'))

                r = requests.post(
                    options["hassio_url"].rstrip("/") + api_ha_url,
                    headers={"Authorization": f"Bearer {options['hassio_key']}"},
                    json=api_ha_data
                )
                print(api_ha_url)
                print(str(api_ha_data))
            except Exception as e:
                print("Error processing tool call:", e)
                r = None  # ensure r is defined

            if "#" in args.get("api_ha_state_value", ""):
                reply = str(args["api_ha_state_value"]).replace("#", "")
                print(reply)
            elif r is not None and r.status_code in (200, 201):
                reply = options["default_reply"][random.randint(0, len(options["default_reply"]) - 1)]
            else:
                reply = None

    return reply


def ha_google_ai(options, function, generation_params, user_input):
    """
    Calls a Google-compatible GenAI REST endpoint using HTTP POST instead of the `genai` Python client.
    """

    # Construct the REST endpoint URL
    url = f"{options['base_url']}{generation_params["model"]}:generateContent?key={options['api_key']}"


    headers = {
        "Content-Type": "application/json",
    }

    payload = {
        "contents": [{"role": "user", "parts": [{"text": user_input}]}],
        "system_instruction": {"parts": [{"text": options["prompt"]}]},
        "tools": [{"function_declarations": [function]}],
        "tool_config": {
            "function_calling_config": {
                "mode": generation_params.get("tool_choice", "AUTO")
            }
        },
        "generationConfig": {
            "maxOutputTokens": generation_params.get("max_tokens"),
            "temperature": generation_params.get("temperature"),
            "candidateCount": generation_params.get("n", 1)
        }
    }

    response = requests.post(url, headers=headers, json=payload)


    response=response.json()
    print(response)
    reply=None
    try:

        candidates = response.get("candidates", [])
        if not candidates:
            print("No candidates in response.")
            return None

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            print("No parts in candidate response.")
            return None

        function_call = parts[0].get("functionCall")
        if function_call:
            args = function_call.get("args", {})

            try:
                api_ha_url = args.get("api_ha_url")
                api_ha_data = json.loads(args.get("api_ha_data", "{}").replace("'", '"'))

                r = requests.post(
                    options["hassio_url"].rstrip("/") + api_ha_url,
                    headers={"Authorization": f"Bearer {options['hassio_key']}"},
                    json=api_ha_data
                )
                print(options["hassio_url"].rstrip("/") + api_ha_url)
                print(str(api_ha_data))
            except Exception as e:
                print("Error processing function args:", e)
                r = None

            if "#" in args.get("api_ha_state_value", ""):
                reply = str(args["api_ha_state_value"]).replace("#", "")
                print(reply)
            elif r is not None and r.status_code in (200, 201):
                reply = options["default_reply"][random.randint(0, len(options["default_reply"]) - 1)]

        else:
            print("No function call found in the response.")
            print(response)

    except Exception as e:
        print("Error parsing response:", e)
        print(response)

    return reply



def HA_AI(core: VACore,phrase:str):
    options = core.plugin_options(modname)

    ha_entities = get_ha_data(options["hassio_url"] + "api/states", options["hassio_key"])
    ha_entities = clean_json(ha_entities, options["entity_id_blacklist"], options["entity_id_whitelist"],
                             options["item_blacklist"])

    TextToHomeAssistantAPI={"name": "TextToHomeAssistantAPI", "description": f"{ha_entities}Based on the information above, you should use user input and create a command for Home Assistant REST API",
                                              "parameters": {"type": "object", "properties": {
                                                  "api_ha_url": {"type": "string",
                                                                 "description": "Ending for Home Assistant REST API url like '/api/services/domain/service'.Don't make up non-existing entities, actions, or parameters; use only entities from the user input. If you can't find existing service in provided by user Home Assistant structure, put 404"},
                                                  "api_ha_data": {"type": "string",
                                                                  "description": "Data for the requested entity to be sent to Home Assistant REST API.Don't make up non-existing entities, actions, or parameters; use only entities from the user input. If you can't find existing entity in provided by user Home Assistant structure, put 404"},
                                                  "api_ha_state_value": {"type": "string",
                                                                         "description": "Current state of the entity. If user asks you to show or tell something like temperature, time, or state of an entity, use the current state of the entity and put its value with a # marker."} },
                                                             "required": ["api_ha_url", "api_ha_data","api_ha_state_value"]}}


    generation_params = {
        "temperature": 0.1,
        "n": 1,
        "max_tokens": 1500,
        "stream": False,
        "tool_choice": "auto",
        "model" : options['AI_model']
    }


    user_input="role:user, input:"+phrase
    try:
        if "google" in options["base_url"]:
            reply = ha_google_ai(options, TextToHomeAssistantAPI,generation_params,user_input)
        else:
            reply = ha_vsegpt_ai(options, TextToHomeAssistantAPI,generation_params,user_input)

        core.play_voice_assistant_speech(reply)
        print(reply)

    except Exception as e:
        reply = "Нейросеть не распознала команду"
        core.play_voice_assistant_speech(reply)
        print("⚠️ Error:", e, "\n")


