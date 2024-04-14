FROM tiangolo/uvicorn-gunicorn:python3.11

COPY ./webapi /app

EXPOSE 8001

RUN --mount=type=cache,target=/root/.cache \
    pip install -r /app/requirements.txt

CMD ["uvicorn", "api_run:app", "--host", "0.0.0.0", "--port", "8001"]