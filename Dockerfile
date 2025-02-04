FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY patentsafe_mcp.py .
COPY mcp-wrapper-linux mcp-wrapper
COPY docker-entrypoint.sh .

RUN pip install bs4>=0.0.2 mcp[cli]>=1.2.1 requests>=2.32.3 && \
    chmod +x docker-entrypoint.sh mcp-wrapper

ENTRYPOINT ["./docker-entrypoint.sh"]
