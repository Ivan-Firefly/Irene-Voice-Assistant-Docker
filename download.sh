#!/bin/bash

# Array of URLs
urls=(
    "https://raw.githubusercontent.com/Ivan-Firefly/Irene-Voice-Assistant-Docker/master/docker-compose.yml"
    "https://raw.githubusercontent.com/Ivan-Firefly/Irene-Voice-Assistant-Docker/master/requirements-docker.txt"
    "https://raw.githubusercontent.com/Ivan-Firefly/Irene-Voice-Assistant-Docker/master/runva_webapi_docker.json"
    "https://raw.githubusercontent.com/Ivan-Firefly/Irene-Voice-Assistant-Docker/master/docker_plugins/core.py"
    "https://raw.githubusercontent.com/Ivan-Firefly/Irene-Voice-Assistant-Docker/master/docker_plugins/plugin_datetime.py"
    "https://raw.githubusercontent.com/Ivan-Firefly/Irene-Voice-Assistant-Docker/master/docker_plugins/plugin_greetings.py"
    "https://raw.githubusercontent.com/Ivan-Firefly/Irene-Voice-Assistant-Docker/master/docker_plugins/plugin_HA_automation_trigger.py"
    "https://raw.githubusercontent.com/Ivan-Firefly/Irene-Voice-Assistant-Docker/master/docker_plugins/plugin_playwav_sounddevice.py"
    "https://raw.githubusercontent.com/Ivan-Firefly/Irene-Voice-Assistant-Docker/master/docker_plugins/plugin_timer.py"
    "https://raw.githubusercontent.com/Ivan-Firefly/Irene-Voice-Assistant-Docker/master/docker_plugins/plugin_tts_console.py"
    "https://raw.githubusercontent.com/Ivan-Firefly/Irene-Voice-Assistant-Docker/master/docker_plugins/plugin_tts_vosk.py"
    "https://raw.githubusercontent.com/Ivan-Firefly/Irene-Voice-Assistant-Docker/master/docker_plugins/plugin_normalizer_prepare.py"
)

# Function to create "docker_plugins" folder
create_plugins_folder() {
    if [ ! -d "docker_plugins" ]; then
        mkdir "docker_plugins"
        echo "Created 'docker_plugins' folder."
    fi
}

# Function to move files with prefix "plugin_" and "core.py" into "docker_plugins" folder
move_plugins_files() {
    create_plugins_folder
    for file in plugin_* core.py; do
        mv "$file" "docker_plugins/"
        echo "Moved $file to 'docker_plugins' folder."
    done
}

# Download function
download_file() {
    url=$1
    filename=$(basename "$url")
    
    echo "Downloading $filename..."
    curl -O "$url"
    echo "Download complete: $filename"
}

# Iterate over array and call download_file for each item
for url in "${urls[@]}"; do
    download_file "$url"
done

# Move files with prefix "plugin_" and "core.py" into "docker_plugins" folder
move_plugins_files
