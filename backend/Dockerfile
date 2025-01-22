FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11 AS python_base
COPY ./requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/requirements.txt

WORKDIR /app
COPY ./app /app/app
COPY ./alembic /app/alembic
COPY ./prestart.sh ./alembic.ini /app/
RUN chmod +x /app/prestart.sh
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

CMD ["/start-reload.sh"]
