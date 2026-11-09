FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend app for shared normalizers and services
COPY ../backend/app /app/backend/app
COPY cloud_scanner.py /app/cloud_scanner.py

CMD ["python", "cloud_scanner.py"]
