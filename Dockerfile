FROM python:3.10-slim

# Chrome과 의존성 설치
RUN apt-get update && apt-get install -y \
    wget \
    libglib2.0-0 \
    libnss3 \
    libfontconfig1 \
    libx11-6 \
    libx11-xcb1 \
    libxi6 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxtst6 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Chrome 설치
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && apt-get install -f -y \
    && rm google-chrome-stable_current_amd64.deb \
    && apt-get clean

# Chrome 설치 확인
RUN google-chrome --version || echo "Chrome installation failed" >&2
RUN which google-chrome || echo "google-chrome not found" >&2
RUN ls -l /usr/bin/google-chrome || echo "/usr/bin/google-chrome not found" >&2

# 작업 디렉토리 설정
WORKDIR /app

# Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY api.py main.py ./
COPY utils/ ./utils/
COPY static/ ./static/

EXPOSE 8000

CMD ["python", "api.py"]
