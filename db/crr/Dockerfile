FROM python:3.12-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN python -c 'import sqlite3' && pip install --no-cache-dir -r requirements.txt
COPY prepare_dataset.py import_inputs.py .
COPY sql/ sql/
ENTRYPOINT ["python", "/app/prepare_dataset.py"]
CMD ["--data-dir", "/data", "--output", "/output/crr.sqlite"]
