FROM python:3.11-slim
LABEL maintainer="daniel.bb0321@gmail.com"

WORKDIR /app
COPY . /app/

RUN pip3 install -r requirements.txt

VOLUME /app
EXPOSE 8000

ENTRYPOINT [ "/bin/bash", "entrypoint.sh" ]
CMD daphne -p 8000 -b 0.0.0.0 testing_game.asgi:application