FROM python:3.11-slim

WORKDIR /app

# Cập nhật hệ thống cơ bản, không cài trình duyệt nặng nề nữa
RUN apt-get update && apt-get install -y \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Cài đặt thư viện Python
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-u", "bot.py"]