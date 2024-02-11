# Docker версия голосового ассистента Ирина

Тут будут описаны только отличия от оригинального репозитория - общее описание, концепцию, доп. плагины - см. тут https://github.com/janvarev/Irene-Voice-Assistant

Docker образ - https://hub.docker.com/r/firefly27/irene-voice-assistant-docker

В качестве "говорилки" (TTS) контейнер работает с **Sirelo (v3,v4), vosk, rhvoice_rest**. Для одноплатников советую выбирать **vosk**, ему должно хватать небольших ресурсов малин/апельсин для генерации голоса с приемлемой задержкой и более-менее адекватным качеством.

В паке `docker_plugins` сложил минимально необходимый набор плагинов (по моим представлениям). Дополнительные плагины можно закинуть в эту же папку и они подтянуться в контейнер. Советую предварительно посмотреть используемые библиотеки, которые используются в новых плагинах. Перед стартом контейнера, новые библиотеки нужно добавить в `requirements-docker.txt`. Если необходимы какие-то системные зависимости, то тут уже только пересобирать контейнер самостоятельно.

Относительно оригинала изменились:
  1. `Dockerfile`
  2. `plugin_tts_console.py` - убран лишний импорт библиотеки pyttsx
  3. `requirements-docker.txt` - оставлен минимальный набор библиотек

Добавлен `docker-compose.yml` для удобного запуска контейнера. 
Перед запуском нужно положить в текущую директорию папку `docker_plugins` (со всем содержимым) и файлы `runva_webapi_docker.json`, `requirements-docker.txt`.
Для удобства есть скрипт `download.sh`, который все скачает и разместит по нужным папкам.

После старта, в текущей директории создается папка `irene_options`, куда выносятся основные настройки Ирины и запущенных плагинов.

Первый запуск контейнера может быть долгим (будет скачиваться модель TTS и устанавливаться все библиотеки из `requirements-docker.txt`) и он пройдет с ошибками (**так и должно быть**):
```
irene-va-docker  | Traceback (most recent call last):
irene-va-docker  |   File "/home/python/irene/vacore.py", line 143, in setup_assistant_voice
irene-va-docker  |     self.playwavs[self.playWavEngineId][0](self)
irene-va-docker  | KeyError: 'consolewav'
```
Нужно остановить контейнер, в автоматически созданной новой папке `irene_options` в `core.json` выставить настройки:
1.  ```"playWavEngineId": "sounddevice" ```
2.  ```"ttsEngineId": "vosk" # или другой TTS (не забудьте добавить нужный плагин в docker_plugins)```

Повторно запускаем контейнер, должен быть быстрый страт без ошибок.

**UPD 21.10.2024**
- Добавлен vosk_asr_server для возможности запуска удаленных клиентов

**Docker версия тонкого/легкого удаленного клиента:**

https://github.com/Ivan-Firefly/Remote-Irene-Docker
