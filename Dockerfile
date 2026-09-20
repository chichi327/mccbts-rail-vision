FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md requirements.txt ./
COPY core core
COPY algorithms algorithms
COPY services services
COPY config config
COPY main.py main.py
COPY scripts scripts

RUN pip install --no-cache-dir -e .

ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "main.py", "--config-dir", "config"]
