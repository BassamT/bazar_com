# order_service/Dockerfile

FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DATABASE orders.db
ENV PORT 5002

EXPOSE ${PORT}

CMD ["python", "-u", "app.py"]
