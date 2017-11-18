FROM python:3.6

ENV PYTHONUNBUFFERED 1

RUN useradd --system app && \
    mkdir /app && \
    chown app:app /app

COPY requirements.txt /app/
COPY requirements_prod.txt /app/
RUN pip install -r /app/requirements_prod.txt

VOLUME ["/app"]
WORKDIR /app
USER app