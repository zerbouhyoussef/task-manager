FROM python:3.9-slim-buster
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5002
ENV PYTHONUNBUFFERED=1
CMD ["python", "-u", "worker.py"]
