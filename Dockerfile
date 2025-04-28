# FST build
FROM python:3.13.3-slim AS builder

RUN mkdir /app

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONBUFFERED=1

COPY requirements.txt /app/

RUN apt update && \
	apt-get install pkg-config build-essential libmariadb-dev -y && \
	pip install --upgrade pip && \
	pip install --no-cache -r requirements.txt
	

# SND build
FROM python:3.13.3-slim

RUN useradd -m -r appuser && \
	mkdir /app/ && \
	chown -R appuser /app

COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app

COPY --chown=appuser:appuser . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONBUFFERED=1

USER appuser

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "./portal/wiki/wsgi:application"]
