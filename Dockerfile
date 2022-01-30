FROM python:3.9

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH $PATH:/root/.cargo/bin

WORKDIR /bot
ENV PYTHONPATH /bot

COPY toxic_bot/requirements.txt /bot/requirements.txt
RUN pip install -r requirements.txt
RUN pip install git+https://github.com/nextcord/nextcord.git@master --force-reinstall --no-deps

COPY toxic_bot /bot/toxic_bot/

