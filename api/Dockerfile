FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
COPY browser/requirements.txt browser/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r browser/requirements.txt

COPY *.py ./
COPY services ./services
COPY browser ./browser
COPY startup.sh .
CMD ["sh", "/app/startup.sh", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
