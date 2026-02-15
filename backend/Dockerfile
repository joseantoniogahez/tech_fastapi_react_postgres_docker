ARG PYTHON_VERSION=3.14.3
FROM python:${PYTHON_VERSION}-slim AS python_base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY ./requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir -r /app/requirements.txt

WORKDIR /app
COPY ./app /app/app
COPY ./alembic /app/alembic
COPY ./prestart.sh ./alembic.ini /app/
RUN chmod +x /app/prestart.sh
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

ENTRYPOINT ["/app/prestart.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
