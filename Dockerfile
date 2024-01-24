FROM --platform=$BUILDPLATFORM curlimages/curl:7.85.0 as vosk-downloader
WORKDIR /home/downloader/models
RUN curl https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip -o ./c611af587fcbdacc16bc7a1c6148916c-vosk-model-small-ru-0.22.zip

FROM python:3.10-slim

WORKDIR /home/python

# Install system dependencies
RUN --mount=type=cache,target=/var/cache,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    libportaudio2 \
    libsndfile1-dev \
    libatomic1 \
    supervisor \
    && rm -rf /var/lib/apt/lists/*


# Copy application files
COPY lingua_franca \
    media \
    mic_client \
    model \
    plugins \
    utils \
    webapi_client \
    requirements-docker.txt \
    localhost.crt \
    localhost.key \
    jaa.py \
    vacore.py \
    runva_webapi.py \
    options_docker \
    runva_webapi_docker.json \
    docker_plugins \
    vosk_asr_server.py \
    supervisord.conf /irene/


COPY --link --chown=1000:1000 --from=vosk-downloader /home/downloader/models/ ./vosk-models/

RUN pip install -r ./irene/requirements.txt \
&& mkdir -p irene/temp

EXPOSE 5003

WORKDIR /home/python/irene

CMD ["bash", "-c", "pip install --no-cache-dir -r requirements.txt && supervisord -n -c supervisord.conf"]
