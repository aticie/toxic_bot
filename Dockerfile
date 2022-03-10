FROM rust:1.59.0-slim

# Install Python
RUN apt-get update && apt-get install -y python3 python3-pip

# Install git
RUN apt-get update && apt-get install -y git

WORKDIR /bot
ENV PYTHONPATH /bot

COPY toxic_bot/requirements.txt /bot/requirements.txt
RUN pip install -r requirements.txt
RUN pip install git+https://github.com/nextcord/nextcord.git@master --force-reinstall --no-deps

COPY toxic_bot /bot/toxic_bot/
COPY assets/fonts /bot/assets/fonts
COPY assets/icons/mods /bot/assets/icons/mods
