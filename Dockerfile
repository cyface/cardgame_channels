FROM python:3.6

ENV PYTHONUNBUFFERED 1

RUN useradd --system app && \
    mkdir /app && \
    chown app:app /app

COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

VOLUME ["/app"]
WORKDIR /app
USER app