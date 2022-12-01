FROM python:3.8-slim AS build-image

USER root
RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential gcc && pip3 install virtualenv

RUN virtualenv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"

ARG USER=docker
ARG UID=1000
ARG GID=1000
# default password for user
ARG PW=docker
RUN useradd -m ${USER} --uid=${UID} && echo "${USER}:${PW}" | chpasswd
RUN mkdir -p /home/${USER}
RUN chown ${USER} /home/${USER}
# Setup default user, when enter docker container
WORKDIR /home/${USER}


COPY setup.py ./setup.py
COPY requirements.txt ./requirements.txt
RUN pip install -e .
COPY ./cerche ./cerche

ENV PYTHONUNBUFFERED 0

USER ${UID}:${GID}

ENTRYPOINT ["/opt/venv/bin/python", "./cerche/main.py"]
CMD ["serve", "--host", "0.0.0.0:8081"]
