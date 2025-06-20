FROM python:3.13.5-slim AS builder
WORKDIR /app

COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.13.5-slim
WORKDIR /app

COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH
ENV TZ=Asia/Tokyo

COPY ./src /app/src/

CMD ["python3", "src/bot.py"]
