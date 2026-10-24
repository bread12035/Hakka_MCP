FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY pyproject.toml .
COPY src ./src
RUN pip install --no-cache-dir --no-deps .
COPY catalog ./catalog

ENV HAKKA_CATALOG=/app/catalog \
    HAKKA_DB=sqlite:////data/hakka.db
VOLUME /data
EXPOSE 8000

CMD ["hakka-mcp", "serve", "--host", "0.0.0.0", "--port", "8000"]
