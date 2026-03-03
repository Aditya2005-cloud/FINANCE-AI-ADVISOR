FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend

WORKDIR /app/backend

COPY backend/requirements.txt /tmp/requirements.txt
RUN grep -v "^-e " /tmp/requirements.txt > /tmp/requirements-docker.txt \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements-docker.txt

COPY backend /app/backend
COPY frontend /app/frontend

RUN sed -i 's|^listen = .*|listen = *:6543|' /app/backend/development.ini

EXPOSE 6543

CMD ["pserve", "development.ini"]
