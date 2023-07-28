FROM rust:slim

# Install Python
RUN apt-get update && apt-get install -y python3 python3-pip sox ffmpeg libcairo2 libcairo2-dev

# Install git
RUN apt-get update && apt-get install -y git

WORKDIR /bot
ENV PYTHONPATH /bot

COPY toxic_bot/requirements.txt /bot/requirements.txt
RUN pip install -r requirements.txt
RUN pip install git+https://github.com/nextcord/nextcord.git@v2.0.0 --force-reinstall --no-deps

COPY toxic_bot /bot/toxic_bot/
COPY assets/fonts /bot/assets/fonts
COPY assets/icons/mods /bot/assets/icons/mods
