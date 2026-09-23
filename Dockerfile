FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt gunicorn==26.2.0

COPY . .

RUN chmod +x docker/entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["./docker/entrypoint.sh"]