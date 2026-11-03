FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN useradd --create-home --uid 10001 appuser

COPY requirements.txt .
# A API não usa o pip em execução. Ele sai da imagem depois de instalar as dependências,
# junto com as CVEs dele e dos componentes que ele embute.
RUN pip install --no-cache-dir -r requirements.txt \
    && pip uninstall -y pip

COPY app ./app

USER appuser
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
