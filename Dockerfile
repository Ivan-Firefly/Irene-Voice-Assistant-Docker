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
COPY lingua_franca irene/lingua_franca
COPY media irene/media
COPY mic_client irene/mic_client
COPY model irene/model
COPY mpcapi irene/mpcapi
COPY plugins irene/plugins
COPY utils irene/utils
COPY webapi_client irene/webapi_client

COPY localhost.crt \
    requirements-docker.txt \
    localhost.key \
    jaa.py \
    vacore.py \
    runva_webapi.py \
    runva_webapi_docker.json \
    vosk_asr_server.py irene/

COPY --link --chown=1000:1000 --from=vosk-downloader /home/downloader/models/ ./vosk-models/

RUN pip install -r irene/requirements-docker.txt \
&& mkdir -p irene/temp

EXPOSE 5003

WORKDIR /home/python/irene

CMD sh -c  "pip install --no-cache-dir -r requirements.txt && python3 runva_webapi.py & python3 vosk_asr_server.py"
