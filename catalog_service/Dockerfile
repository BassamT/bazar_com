# catalog_service/Dockerfile

FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose the port (this is optional as ports are mapped in docker-compose)
EXPOSE ${PORT}

CMD ["python", "app.py"]
