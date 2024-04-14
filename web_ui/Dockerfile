FROM tiangolo/uvicorn-gunicorn:python3.11

COPY ./webui /app

EXPOSE 8000

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]